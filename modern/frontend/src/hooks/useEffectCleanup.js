import { useEffect, useRef, useCallback } from "react";

/**
 * Effect cleanup utilities for preventing memory leaks in React components
 * Provides comprehensive cleanup for common sources of memory leaks
 */

// Debounced effect hook with automatic cleanup
export const useDebouncedEffect = (effect, dependencies, delay = 300) => {
  const timeoutRef = useRef(null);
  const cleanupRef = useRef(null);

  useEffect(() => {
    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout
    timeoutRef.current = setTimeout(() => {
      // Run the effect and store cleanup function if returned
      const cleanup = effect();
      if (typeof cleanup === "function") {
        cleanupRef.current = cleanup;
      }
    }, delay);

    // Cleanup function
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (cleanupRef.current) {
        cleanupRef.current();
        cleanupRef.current = null;
      }
    };
  }, [...dependencies, delay]);
};

// AbortController hook for cancelling fetch requests
export const useAbortController = () => {
  const controllerRef = useRef(null);

  const createController = useCallback(() => {
    // Abort existing controller
    if (controllerRef.current) {
      controllerRef.current.abort();
    }

    // Create new controller
    controllerRef.current = new AbortController();
    return controllerRef.current;
  }, []);

  const abort = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (controllerRef.current) {
        controllerRef.current.abort();
      }
    };
  }, []);

  return { createController, abort, controller: controllerRef.current };
};

// WebSocket hook with automatic cleanup
export const useWebSocket = (url, options = {}) => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isUnmountedRef = useRef(false);

  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
    ...wsOptions
  } = options;

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = (event) => {
        if (onOpen && !isUnmountedRef.current) {
          onOpen(event);
        }
      };

      wsRef.current.onmessage = (event) => {
        if (onMessage && !isUnmountedRef.current) {
          onMessage(event);
        }
      };

      wsRef.current.onclose = (event) => {
        if (onClose && !isUnmountedRef.current) {
          onClose(event);
        }

        // Auto-reconnect logic
        if (!isUnmountedRef.current && !event.wasClean) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      };

      wsRef.current.onerror = (event) => {
        if (onError && !isUnmountedRef.current) {
          onError(event);
        }
      };
    } catch (error) {
      if (onError && !isUnmountedRef.current) {
        onError(error);
      }
    }
  }, [url, onMessage, onOpen, onClose, onError, reconnectDelay]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "Component unmounting");
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        typeof data === "string" ? data : JSON.stringify(data)
      );
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      isUnmountedRef.current = true;
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    sendMessage,
    disconnect,
    reconnect: connect,
    readyState: wsRef.current?.readyState || WebSocket.CONNECTING,
  };
};

// Event listener hook with automatic cleanup
export const useEventListener = (
  eventName,
  handler,
  element = window,
  options = {}
) => {
  const savedHandler = useRef();

  // Update ref.current value if handler changes
  useEffect(() => {
    savedHandler.current = handler;
  }, [handler]);

  useEffect(() => {
    // Make sure element supports addEventListener
    const isSupported = element && element.addEventListener;
    if (!isSupported) return;

    // Create event listener that calls handler function stored in ref
    const eventListener = (event) => savedHandler.current(event);

    // Add event listener
    element.addEventListener(eventName, eventListener, options);

    // Remove event listener on cleanup
    return () => {
      element.removeEventListener(eventName, eventListener, options);
    };
  }, [eventName, element, options]);
};

// Intersection Observer hook with cleanup
export const useIntersectionObserver = (callback, options = {}) => {
  const observerRef = useRef(null);
  const elementsRef = useRef(new Set());

  const observe = useCallback(
    (element) => {
      if (!element) return;

      if (!observerRef.current) {
        observerRef.current = new IntersectionObserver(callback, options);
      }

      observerRef.current.observe(element);
      elementsRef.current.add(element);
    },
    [callback, options]
  );

  const unobserve = useCallback((element) => {
    if (observerRef.current && element) {
      observerRef.current.unobserve(element);
      elementsRef.current.delete(element);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
      elementsRef.current.clear();
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { observe, unobserve, disconnect };
};

// Async effect hook with cancellation support
export const useAsyncEffect = (asyncEffect, dependencies, onError) => {
  const { createController } = useAbortController();

  useEffect(() => {
    const controller = createController();

    const runAsync = async () => {
      try {
        await asyncEffect(controller.signal);
      } catch (error) {
        // Only handle error if not aborted
        if (error.name !== "AbortError" && onError) {
          onError(error);
        }
      }
    };

    runAsync();

    return () => {
      controller.abort();
    };
  }, dependencies);
};

// Timer hook with automatic cleanup
export const useTimer = (callback, delay, immediate = false) => {
  const callbackRef = useRef(callback);
  const timeoutRef = useRef(null);
  const isRunningRef = useRef(false);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const start = useCallback(() => {
    if (isRunningRef.current) return;

    isRunningRef.current = true;
    timeoutRef.current = setTimeout(() => {
      callbackRef.current();
      isRunningRef.current = false;
    }, delay);
  }, [delay]);

  const stop = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
      isRunningRef.current = false;
    }
  }, []);

  const reset = useCallback(() => {
    stop();
    start();
  }, [start, stop]);

  useEffect(() => {
    if (immediate) {
      start();
    }
    return stop;
  }, [immediate, start, stop]);

  return { start, stop, reset, isRunning: isRunningRef.current };
};

// Interval hook with automatic cleanup
export const useInterval = (callback, delay, immediate = false) => {
  const callbackRef = useRef(callback);
  const intervalRef = useRef(null);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const start = useCallback(() => {
    if (intervalRef.current) return; // Already running

    if (immediate) {
      callbackRef.current();
    }

    intervalRef.current = setInterval(() => {
      callbackRef.current();
    }, delay);
  }, [delay, immediate]);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    start();
    return stop;
  }, [start, stop]);

  return { start, stop };
};

// Media query hook with cleanup
export const useMediaQuery = (query) => {
  const [matches, setMatches] = useState(false);
  const mediaQueryRef = useRef(null);

  useEffect(() => {
    mediaQueryRef.current = window.matchMedia(query);
    setMatches(mediaQueryRef.current.matches);

    const handler = (event) => setMatches(event.matches);

    mediaQueryRef.current.addEventListener("change", handler);

    return () => {
      if (mediaQueryRef.current) {
        mediaQueryRef.current.removeEventListener("change", handler);
      }
    };
  }, [query]);

  return matches;
};

// Local storage hook with cleanup
export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value) => {
      try {
        const valueToStore =
          value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.localStorage.setItem(key, JSON.stringify(valueToStore));

        // Dispatch storage event for cross-tab synchronization
        window.dispatchEvent(
          new StorageEvent("storage", {
            key,
            newValue: JSON.stringify(valueToStore),
            oldValue: JSON.stringify(storedValue),
            storageArea: window.localStorage,
            url: window.location.href,
          })
        );
      } catch (error) {
        console.error(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // Listen for external storage changes
  useEventListener("storage", (event) => {
    if (event.key === key && event.newValue !== null) {
      try {
        setStoredValue(JSON.parse(event.newValue));
      } catch (error) {
        console.error(`Error parsing localStorage key "${key}":`, error);
      }
    }
  });

  return [storedValue, setValue];
};

// Component unmount detector
export const useUnmountDetector = () => {
  const isUnmountedRef = useRef(false);

  useEffect(() => {
    return () => {
      isUnmountedRef.current = true;
    };
  }, []);

  return isUnmountedRef;
};

// Performance monitoring hook
export const usePerformanceMonitor = (componentName, dependencies = []) => {
  const renderCountRef = useRef(0);
  const lastRenderTimeRef = useRef(0);

  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      renderCountRef.current += 1;
      const now = performance.now();
      const renderTime = now - lastRenderTimeRef.current;

      console.log(`[Performance] ${componentName}:`, {
        renderCount: renderCountRef.current,
        renderTime: renderTime.toFixed(2) + "ms",
        dependencies,
      });

      lastRenderTimeRef.current = now;
    }
  }, dependencies);
};

export default {
  useDebouncedEffect,
  useAbortController,
  useWebSocket,
  useEventListener,
  useIntersectionObserver,
  useAsyncEffect,
  useTimer,
  useInterval,
  useMediaQuery,
  useLocalStorage,
  useUnmountDetector,
  usePerformanceMonitor,
};
