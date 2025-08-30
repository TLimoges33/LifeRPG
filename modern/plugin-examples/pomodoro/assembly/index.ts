import { PluginContext } from "@liferpg/plugin-sdk";

/**
 * Pomodoro Timer Plugin for LifeRPG
 * 
 * This plugin adds a Pomodoro timer widget to the dashboard
 * and integrates with habit tracking.
 */
export function initialize(context: PluginContext): void {
  context.log("Pomodoro plugin initialized");
  
  // Register a dashboard widget with a Pomodoro timer
  context.api.registerDashboardWidget(
    "pomodoro-timer",
    "Pomodoro Timer",
    `
    <div class="p-4 bg-card border border-border rounded-lg">
      <div class="text-center mb-4">
        <div class="text-3xl font-bold timer-display">25:00</div>
        <div class="text-sm text-muted-foreground timer-status">Ready to focus</div>
      </div>
      
      <div class="flex justify-between mb-4">
        <button class="bg-primary text-primary-foreground px-3 py-2 rounded-md timer-start">Start</button>
        <button class="bg-secondary text-secondary-foreground px-3 py-2 rounded-md timer-pause" disabled>Pause</button>
        <button class="bg-secondary text-secondary-foreground px-3 py-2 rounded-md timer-reset">Reset</button>
      </div>
      
      <div class="flex justify-between text-sm">
        <div>
          <span class="font-medium">Mode:</span>
          <select class="ml-2 border border-border rounded bg-background timer-mode">
            <option value="25" selected>Pomodoro (25m)</option>
            <option value="5">Short Break (5m)</option>
            <option value="15">Long Break (15m)</option>
          </select>
        </div>
        
        <div class="pomodoro-count">
          <span class="font-medium">Today:</span>
          <span class="ml-2">0 pomodoros</span>
        </div>
      </div>
    </div>
    
    <script>
      // Get DOM elements
      const timerDisplay = document.querySelector('.timer-display');
      const timerStatus = document.querySelector('.timer-status');
      const startButton = document.querySelector('.timer-start');
      const pauseButton = document.querySelector('.timer-pause');
      const resetButton = document.querySelector('.timer-reset');
      const modeSelect = document.querySelector('.timer-mode');
      const pomodoroCount = document.querySelector('.pomodoro-count span:last-child');
      
      // Timer state
      let timeLeft = 25 * 60;
      let timerId = null;
      let isRunning = false;
      let isPaused = false;
      let completedPomodoros = 0;
      
      // Format time as MM:SS
      function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return \`\${mins.toString().padStart(2, '0')}:\${secs.toString().padStart(2, '0')}\`;
      }
      
      // Update timer display
      function updateDisplay() {
        timerDisplay.textContent = formatTime(timeLeft);
      }
      
      // Start timer
      function startTimer() {
        if (isRunning) return;
        
        isRunning = true;
        isPaused = false;
        
        startButton.disabled = true;
        pauseButton.disabled = false;
        modeSelect.disabled = true;
        
        timerStatus.textContent = 'Focus time!';
        
        timerId = setInterval(() => {
          timeLeft--;
          updateDisplay();
          
          if (timeLeft <= 0) {
            completeTimer();
          }
        }, 1000);
      }
      
      // Pause timer
      function pauseTimer() {
        if (!isRunning || isPaused) return;
        
        clearInterval(timerId);
        isPaused = true;
        
        startButton.disabled = false;
        startButton.textContent = 'Resume';
        
        timerStatus.textContent = 'Paused';
      }
      
      // Complete timer
      function completeTimer() {
        clearInterval(timerId);
        isRunning = false;
        
        // If it was a pomodoro (not a break)
        if (modeSelect.value === '25') {
          completedPomodoros++;
          pomodoroCount.textContent = \`\${completedPomodoros} pomodoros\`;
          
          // Show notification
          if (Notification.permission === 'granted') {
            new Notification('Pomodoro Complete!', {
              body: 'Time for a break. You\'ve earned it!',
              icon: '/logo.png'
            });
          }
          
          // Auto-switch to break
          modeSelect.value = completedPomodoros % 4 === 0 ? '15' : '5';
          timeLeft = parseInt(modeSelect.value) * 60;
          timerStatus.textContent = completedPomodoros % 4 === 0 ? 
            'Time for a long break!' : 'Time for a short break!';
        } else {
          // It was a break, switch back to pomodoro
          modeSelect.value = '25';
          timeLeft = 25 * 60;
          timerStatus.textContent = 'Ready to focus again?';
        }
        
        updateDisplay();
        resetButtons();
      }
      
      // Reset timer
      function resetTimer() {
        clearInterval(timerId);
        isRunning = false;
        isPaused = false;
        
        timeLeft = parseInt(modeSelect.value) * 60;
        updateDisplay();
        
        timerStatus.textContent = 'Ready to focus';
        resetButtons();
      }
      
      // Reset button state
      function resetButtons() {
        startButton.disabled = false;
        startButton.textContent = 'Start';
        pauseButton.disabled = true;
        modeSelect.disabled = false;
      }
      
      // Event listeners
      startButton.addEventListener('click', () => {
        if (isPaused) {
          isRunning = false;
          startTimer();
        } else {
          startTimer();
        }
      });
      
      pauseButton.addEventListener('click', pauseTimer);
      resetButton.addEventListener('click', resetTimer);
      
      modeSelect.addEventListener('change', () => {
        timeLeft = parseInt(modeSelect.value) * 60;
        updateDisplay();
        
        if (modeSelect.value === '25') {
          timerStatus.textContent = 'Ready to focus';
        } else if (modeSelect.value === '5') {
          timerStatus.textContent = 'Short break time';
        } else {
          timerStatus.textContent = 'Long break time';
        }
      });
      
      // Request notification permission
      if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
        Notification.requestPermission();
      }
      
      // Initialize
      updateDisplay();
    </script>
    `
  );
  
  // Register a menu item for Pomodoro settings
  context.api.registerMenuItem(
    "pomodoro-settings",
    "Pomodoro Settings",
    "/settings/pomodoro"
  );
  
  // Listen for habit completion events
  // (Not implemented in this example as event system is pending)
}
