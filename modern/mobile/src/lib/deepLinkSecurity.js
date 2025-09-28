/**
 * Deep Link Security utilities for mobile application
 */

// Deep link security configuration
const DEEP_LINK_CONFIG = {
  // Allowed URL schemes
  allowedSchemes: ["wizardsgrimoire", "https"],

  // Allowed hosts for https links
  allowedHosts: [
    "wizardsgrimoire.com",
    "app.wizardsgrimoire.com",
    "api.wizardsgrimoire.com",
  ],

  // Maximum parameter lengths
  maxParamLength: 1000,
  maxParamCount: 20,

  // Sensitive parameter patterns (never allow in deep links)
  sensitivePatterns: [
    /password/i,
    /token/i,
    /secret/i,
    /key/i,
    /auth/i,
    /session/i,
    /credit/i,
    /payment/i,
  ],

  // Allowed routes and their parameter validation rules
  allowedRoutes: {
    habits: {
      params: ["id", "action"],
      validation: {
        id: /^\d+$/,
        action: /^(view|edit|complete)$/,
      },
    },
    projects: {
      params: ["id", "action"],
      validation: {
        id: /^\d+$/,
        action: /^(view|edit|archive)$/,
      },
    },
    profile: {
      params: ["section"],
      validation: {
        section: /^(general|preferences|security)$/,
      },
    },
    share: {
      params: ["type", "code"],
      validation: {
        type: /^(habit|project)$/,
        code: /^[a-zA-Z0-9]{8,16}$/,
      },
    },
  },
};

class DeepLinkValidator {
  static validateDeepLink(url) {
    try {
      const parsedUrl = new URL(url);

      // Validate scheme
      if (!this.validateScheme(parsedUrl.protocol.slice(0, -1))) {
        throw new Error(`Invalid URL scheme: ${parsedUrl.protocol}`);
      }

      // Validate host for https links
      if (
        parsedUrl.protocol === "https:" &&
        !this.validateHost(parsedUrl.hostname)
      ) {
        throw new Error(`Invalid host: ${parsedUrl.hostname}`);
      }

      // Extract and validate route
      const route = this.extractRoute(parsedUrl.pathname);
      if (!this.validateRoute(route)) {
        throw new Error(`Invalid route: ${route}`);
      }

      // Validate parameters
      const params = this.extractParams(parsedUrl.searchParams);
      if (!this.validateParams(route, params)) {
        throw new Error("Invalid parameters");
      }

      // Check for sensitive data
      if (this.containsSensitiveData(url)) {
        throw new Error("Deep link contains sensitive data");
      }

      return {
        valid: true,
        route: route,
        params: params,
        sanitizedUrl: this.sanitizeUrl(parsedUrl),
      };
    } catch (error) {
      console.error("Deep link validation failed:", error.message);
      return {
        valid: false,
        error: error.message,
        route: null,
        params: null,
      };
    }
  }

  static validateScheme(scheme) {
    return DEEP_LINK_CONFIG.allowedSchemes.includes(scheme);
  }

  static validateHost(hostname) {
    return DEEP_LINK_CONFIG.allowedHosts.includes(hostname);
  }

  static extractRoute(pathname) {
    // Remove leading slash and extract first path segment
    const segments = pathname.replace(/^\/+/, "").split("/");
    return segments[0] || "home";
  }

  static validateRoute(route) {
    return (
      Object.keys(DEEP_LINK_CONFIG.allowedRoutes).includes(route) ||
      route === "home"
    );
  }

  static extractParams(searchParams) {
    const params = {};
    let paramCount = 0;

    for (const [key, value] of searchParams.entries()) {
      paramCount++;

      // Check parameter limits
      if (paramCount > DEEP_LINK_CONFIG.maxParamCount) {
        throw new Error("Too many parameters");
      }

      if (value.length > DEEP_LINK_CONFIG.maxParamLength) {
        throw new Error(`Parameter ${key} too long`);
      }

      params[key] = value;
    }

    return params;
  }

  static validateParams(route, params) {
    const routeConfig = DEEP_LINK_CONFIG.allowedRoutes[route];

    if (!routeConfig) {
      return Object.keys(params).length === 0; // No params for unknown routes
    }

    // Check allowed parameters
    for (const paramName of Object.keys(params)) {
      if (!routeConfig.params.includes(paramName)) {
        throw new Error(
          `Parameter ${paramName} not allowed for route ${route}`
        );
      }

      // Validate parameter format
      const validation = routeConfig.validation[paramName];
      if (validation && !validation.test(params[paramName])) {
        throw new Error(`Invalid format for parameter ${paramName}`);
      }
    }

    return true;
  }

  static containsSensitiveData(url) {
    const urlLower = url.toLowerCase();

    return DEEP_LINK_CONFIG.sensitivePatterns.some((pattern) =>
      pattern.test(urlLower)
    );
  }

  static sanitizeUrl(parsedUrl) {
    // Remove any potentially dangerous characters
    const sanitizedPathname = parsedUrl.pathname.replace(/[<>'"]/g, "");

    // Rebuild URL with sanitized components
    const sanitized = new URL(parsedUrl.origin + sanitizedPathname);

    // Copy safe parameters only
    for (const [key, value] of parsedUrl.searchParams.entries()) {
      const sanitizedKey = key.replace(/[<>'"]/g, "");
      const sanitizedValue = value.replace(/[<>'"]/g, "");

      if (sanitizedKey && sanitizedValue) {
        sanitized.searchParams.set(sanitizedKey, sanitizedValue);
      }
    }

    return sanitized.toString();
  }

  // Generate secure share codes for deep links
  static generateShareCode(type, resourceId) {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 10);
    const typePrefix = type.substring(0, 2);

    return `${typePrefix}${timestamp}${random}`.substring(0, 16);
  }

  // Validate share codes
  static validateShareCode(code, type) {
    if (!/^[a-zA-Z0-9]{8,16}$/.test(code)) {
      return false;
    }

    const typePrefix = type.substring(0, 2);
    return code.startsWith(typePrefix);
  }
}

// Deep link handler for mobile app
class DeepLinkHandler {
  constructor() {
    this.handlers = new Map();
    this.setupDefaultHandlers();
  }

  setupDefaultHandlers() {
    this.handlers.set("habits", this.handleHabitsLink.bind(this));
    this.handlers.set("projects", this.handleProjectsLink.bind(this));
    this.handlers.set("profile", this.handleProfileLink.bind(this));
    this.handlers.set("share", this.handleShareLink.bind(this));
  }

  async handleDeepLink(url) {
    console.log("Processing deep link:", url);

    // Validate the deep link
    const validation = DeepLinkValidator.validateDeepLink(url);

    if (!validation.valid) {
      console.error("Invalid deep link:", validation.error);
      return this.handleInvalidLink(validation.error);
    }

    // Get handler for route
    const handler = this.handlers.get(validation.route);

    if (handler) {
      try {
        await handler(validation.params, validation.sanitizedUrl);
      } catch (error) {
        console.error("Deep link handler error:", error);
        return this.handleHandlerError(error);
      }
    } else {
      // Default to home screen
      return this.navigateToHome();
    }
  }

  async handleHabitsLink(params, url) {
    const habitId = params.id;
    const action = params.action || "view";

    // Navigate to habits with specific habit and action
    console.log(`Navigating to habit ${habitId} with action ${action}`);

    // Implementation would navigate to the appropriate screen
    // navigation.navigate('Habits', { habitId, action });
  }

  async handleProjectsLink(params, url) {
    const projectId = params.id;
    const action = params.action || "view";

    console.log(`Navigating to project ${projectId} with action ${action}`);

    // navigation.navigate('Projects', { projectId, action });
  }

  async handleProfileLink(params, url) {
    const section = params.section || "general";

    console.log(`Navigating to profile section: ${section}`);

    // navigation.navigate('Profile', { section });
  }

  async handleShareLink(params, url) {
    const type = params.type;
    const code = params.code;

    if (!DeepLinkValidator.validateShareCode(code, type)) {
      throw new Error("Invalid share code");
    }

    console.log(`Processing share link for ${type} with code ${code}`);

    // Handle shared content
    // shareService.processShareCode(type, code);
  }

  handleInvalidLink(error) {
    console.warn("Invalid deep link, redirecting to home:", error);
    return this.navigateToHome();
  }

  handleHandlerError(error) {
    console.error("Deep link handler failed, redirecting to home:", error);
    return this.navigateToHome();
  }

  navigateToHome() {
    console.log("Navigating to home screen");
    // navigation.navigate('Home');
  }
}

// Export for use in React Native app
export { DeepLinkValidator, DeepLinkHandler, DEEP_LINK_CONFIG };
