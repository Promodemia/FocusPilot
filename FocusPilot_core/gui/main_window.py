"""Main window for FocusPilot GUI using Tkinter"""
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    def __init__(self, coordinator=None, config=None):
        super().__init__()
        self.coordinator = coordinator
        self.config = config or {}
        
        self.title("FocusPilot - Activity Monitor")
        self.geometry("1000x700")
        
        # Theme
        style = ttk.Style()
        style.theme_use("clam")
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Daily Plan
        self.plan_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plan_tab, text="Daily Plan")
        self._setup_plan_tab()
        
        # Tab 2: Statistics
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text="Statistics")
        self._setup_stats_tab()
        
        # Tab 3: Current Status
        self.status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.status_tab, text="Status")
        self._setup_status_tab()
        
        # Tab 4: Settings
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        self._setup_settings_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Start update loop
        self.update_loop()
        
    def _setup_plan_tab(self):
        """Setup Daily Plan tab with text editor"""
        frame = ttk.Frame(self.plan_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        label = ttk.Label(frame, text="Daily Plan", font=("Arial", 12, "bold"))
        label.pack(pady=5, anchor=tk.W)
        
        instructions = ttk.Label(
            frame, 
            text="Enter your daily plan (one activity per line).\nExample: 9:00-10:00 Work on project\n10:00-10:15 Break",
            font=("Arial", 9)
        )
        instructions.pack(pady=5, anchor=tk.W)
        
        self.plan_text = scrolledtext.ScrolledText(frame, height=20, width=80, wrap=tk.WORD)
        self.plan_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        btn_save = ttk.Button(button_frame, text="Save Plan", command=self._save_plan)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        btn_clear = ttk.Button(button_frame, text="Clear", command=self._clear_plan)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        btn_load = ttk.Button(button_frame, text="Load Today's Plan", command=self._load_plan)
        btn_load.pack(side=tk.LEFT, padx=5)
    
    def _setup_stats_tab(self):
        """Setup Statistics tab with category breakdown"""
        frame = ttk.Frame(self.stats_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        label = ttk.Label(frame, text="Activity Summary Today", font=("Arial", 12, "bold"))
        label.pack(pady=5, anchor=tk.W)
        
        # Create treeview table
        self.stats_tree = ttk.Treeview(
            frame, 
            columns=("Category", "Time (min)", "Percentage"), 
            height=10,
            show="headings"
        )
        self.stats_tree.column("Category", width=200, anchor=tk.W)
        self.stats_tree.column("Time (min)", width=150, anchor=tk.CENTER)
        self.stats_tree.column("Percentage", width=150, anchor=tk.CENTER)
        self.stats_tree.heading("Category", text="Category")
        self.stats_tree.heading("Time (min)", text="Time (min)")
        self.stats_tree.heading("Percentage", text="Percentage")
        self.stats_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.stats_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_tree.configure(yscroll=scrollbar.set)
        
        # Initialize rows
        self.categories = ["work", "communication", "distraction", "break", "neutral", "unknown"]
        for cat in self.categories:
            self.stats_tree.insert("", tk.END, values=(cat.title(), "0", "0%"))
        
        # Export button
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="📥 Export Report", command=self._export_report).pack(side=tk.LEFT, padx=5)
    
    def _setup_status_tab(self):
        """Setup Current Status tab"""
        frame = ttk.Frame(self.status_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        label = ttk.Label(frame, text="Current Activity", font=("Arial", 12, "bold"))
        label.pack(pady=10, anchor=tk.W)
        
        # Activity display
        self.status_label = ttk.Label(
            frame, 
            text="No activity detected", 
            font=("Arial", 16, "bold"),
            foreground="blue"
        )
        self.status_label.pack(pady=10)
        
        self.confidence_label = ttk.Label(
            frame, 
            text="Confidence: -", 
            font=("Arial", 12)
        )
        self.confidence_label.pack(pady=5)
        
        self.app_label = ttk.Label(
            frame, 
            text="App: -", 
            font=("Arial", 12)
        )
        self.app_label.pack(pady=5)
        
        self.duration_label = ttk.Label(
            frame, 
            text="Duration: 0:00", 
            font=("Arial", 12)
        )
        self.duration_label.pack(pady=5)
        
        # Progress bar for work time
        ttk.Label(frame, text="Work Progress Today:", font=("Arial", 11, "bold")).pack(pady=(20, 5), anchor=tk.W)
        self.work_progress = ttk.Progressbar(frame, length=400, mode='determinate', value=0)
        self.work_progress.pack(fill=tk.X, pady=5)
        self.work_progress_label = ttk.Label(frame, text="0 minutes")
        self.work_progress_label.pack(anchor=tk.W)
        
        # Control buttons
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=20)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", command=self._start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", command=self._stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        frame.pack_propagate(False)
    
    def _setup_settings_tab(self):
        """Setup Settings tab"""
        frame = ttk.Frame(self.settings_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        label = ttk.Label(frame, text="Settings", font=("Arial", 12, "bold"))
        label.pack(pady=10, anchor=tk.W)
        
        # Distraction threshold slider
        threshold_frame = ttk.LabelFrame(frame, text="Distraction Alert Settings", padding=10)
        threshold_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(threshold_frame, text="Alert after (minutes):").pack(anchor=tk.W)
        
        slider_frame = ttk.Frame(threshold_frame)
        slider_frame.pack(fill=tk.X, pady=5)
        
        self.threshold_slider = ttk.Scale(slider_frame, from_=1, to=30, orient=tk.HORIZONTAL)
        self.threshold_slider.set(2)
        self.threshold_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.threshold_label = ttk.Label(slider_frame, text="2 min", width=6)
        self.threshold_label.pack(side=tk.LEFT, padx=5)
        self.threshold_slider.configure(command=self._update_threshold_label)
        
        # Notifications checkbox
        notify_frame = ttk.LabelFrame(frame, text="Notifications", padding=10)
        notify_frame.pack(fill=tk.X, pady=10)
        
        self.notifications_var = tk.BooleanVar(value=True)
        notifications_cb = ttk.Checkbutton(
            notify_frame, 
            text="Enable Distraction Notifications", 
            variable=self.notifications_var
        )
        notifications_cb.pack(anchor=tk.W)
        
        self.tray_var = tk.BooleanVar(value=True)
        tray_cb = ttk.Checkbutton(
            notify_frame, 
            text="Show Tray Icon", 
            variable=self.tray_var
        )
        tray_cb.pack(anchor=tk.W)
        
        # Save settings button
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=20)
        ttk.Button(btn_frame, text="Save Settings", command=self._save_settings).pack(side=tk.LEFT, padx=5)
        
        # Info
        info_frame = ttk.LabelFrame(frame, text="Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        info_text = ttk.Label(
            info_frame,
            text="• FocusPilot monitors your activity from ActivityWatch\n"
                 "• Activities are classified into 6 categories\n"
                 "• Alerts appear when you deviate from planned activity\n"
                 "• Data is saved daily in focuspilot.db\n"
                 "• Use Daily Plan tab to define your work schedule",
            font=("Arial", 9),
            justify=tk.LEFT
        )
        info_text.pack(anchor=tk.NW)
    
    def _save_plan(self):
        """Save daily plan"""
        plan_text = self.plan_text.get("1.0", tk.END).strip()
        if not plan_text:
            messagebox.showwarning("Empty", "Plan is empty")
            return
        
        if self.coordinator:
            try:
                self.coordinator.set_daily_plan(plan_text)
                self.status_var.set("Plan saved successfully!")
                messagebox.showinfo("Success", "Daily plan saved!")
            except Exception as e:
                logger.error(f"Error saving plan: {e}")
                messagebox.showerror("Error", f"Failed to save plan: {e}")
    
    def _clear_plan(self):
        """Clear daily plan"""
        if messagebox.askyesno("Clear", "Clear the plan?"):
            self.plan_text.delete("1.0", tk.END)
    
    def _load_plan(self):
        """Load today's plan"""
        if not self.coordinator:
            messagebox.showwarning("Error", "Coordinator not available")
            return
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            plan = self.coordinator.db_manager.get_daily_plan(today)
            
            if plan:
                self.plan_text.delete("1.0", tk.END)
                self.plan_text.insert("1.0", plan)
                self.status_var.set("Plan loaded from today")
            else:
                messagebox.showinfo("Info", "No plan found for today")
        except Exception as e:
            logger.error(f"Error loading plan: {e}")
            messagebox.showerror("Error", f"Failed to load plan: {e}")
    
    def _update_threshold_label(self, value):
        """Update threshold label when slider changes"""
        val = int(float(value))
        self.threshold_label.config(text=f"{val} min")
    
    def _save_settings(self):
        """Save settings"""
        threshold = int(float(self.threshold_slider.get()))
        notifications = self.notifications_var.get()
        
        # Save to config
        if self.config is not None:
            self.config['distraction_threshold_seconds'] = threshold * 60
            self.config['enable_notifications'] = notifications
        
        self.status_var.set(f"Settings saved: threshold={threshold}min, notifications={notifications}")
        logger.info(f"Settings saved: threshold={threshold}min, notifications={notifications}")
    
    def _start_monitoring(self):
        """Start monitoring"""
        if self.coordinator and not getattr(self.coordinator, 'is_running', False):
            self.coordinator.start_coordinator()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("Monitoring started")
    
    def _stop_monitoring(self):
        """Stop monitoring"""
        if self.coordinator and getattr(self.coordinator, 'is_running', False):
            self.coordinator.stop_coordinator()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("Monitoring stopped")
    
    def _export_report(self):
        """Export statistics report"""
        if not self.coordinator:
            messagebox.showwarning("Error", "Coordinator not available")
            return
        
        try:
            stats = getattr(self.coordinator, 'daily_stats', {})
            total_time = sum(stats.values()) / 60  # Convert to minutes
            
            report = "FocusPilot Daily Report\n"
            report += f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            report += f"Total time tracked: {int(total_time)} minutes\n\n"
            report += "Category breakdown:\n"
            
            for cat in self.categories:
                seconds = stats.get(cat, 0)
                minutes = int(seconds / 60)
                pct = 100 * minutes / total_time if total_time > 0 else 0
                report += f"  {cat.title()}: {minutes} min ({pct:.1f}%)\n"
            
            # Save to file
            filename = f"focuspilot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(report)
            
            messagebox.showinfo("Export", f"Report saved to {filename}")
            self.status_var.set(f"Report exported to {filename}")
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            messagebox.showerror("Error", f"Failed to export report: {e}")
    
    def update_stats(self):
        """Update statistics from coordinator"""
        if not self.coordinator:
            return
        
        try:
            stats = getattr(self.coordinator, 'daily_stats', {})
            total_time = sum(stats.values())
            
            # Update stats table
            for i, cat in enumerate(self.categories):
                seconds = stats.get(cat, 0)
                minutes = int(seconds / 60)
                pct = 100 * seconds / total_time if total_time > 0 else 0
                
                # Update tree items
                items = self.stats_tree.get_children()
                if i < len(items):
                    self.stats_tree.item(items[i], values=(cat.title(), str(minutes), f"{pct:.0f}%"))
        except Exception as e:
            logger.debug(f"Error updating stats: {e}")
    
    def update_status(self):
        """Update current status"""
        if not self.coordinator:
            return
        
        try:
            # Get last activity
            category = getattr(self.coordinator, 'current_category', 'unknown')
            confidence = getattr(self.coordinator, 'current_confidence', 0)
            
            self.status_label.config(text=f"Activity: {category.upper()}")
            self.confidence_label.config(text=f"Confidence: {confidence*100:.0f}%")
            
            # Update work progress
            stats = getattr(self.coordinator, 'daily_stats', {})
            work_seconds = stats.get('work', 0)
            work_minutes = int(work_seconds / 60)
            self.work_progress.config(value=min(work_minutes, 480))  # Max 8 hours
            self.work_progress_label.config(text=f"{work_minutes} minutes")
            
            # Update stats
            self.update_stats()
        except Exception as e:
            logger.debug(f"Error updating status: {e}")
    
    def update_loop(self):
        """Update UI every second"""
        self.update_status()
        self.after(1000, self.update_loop)
