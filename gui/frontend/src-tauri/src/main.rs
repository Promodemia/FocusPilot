#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::{
    api::notification::Notification, CustomMenuItem, Menu, MenuItem, Submenu, SystemTray,
    SystemTrayEvent, SystemTrayMenu,
};
use std::process::Command;
use std::sync::Arc;
use tokio::sync::Mutex;

mod commands;
mod backend;

use commands::*;
use backend::*;

fn main() {
    // Tauri menu
    let tray_menu = SystemTrayMenu::new()
        .add_item(CustomMenuItem::new("show", "Show Window"))
        .add_item(CustomMenuItem::new("pause", "Pause Monitoring"))
        .add_native_item(MenuItem::Separator)
        .add_item(CustomMenuItem::new("quit", "Quit"));

    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                "show" => {
                    if let Some(window) = app.get_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                "pause" => {
                    let window = app.get_window("main");
                    if let Some(w) = window {
                        let _ = w.emit_all("toggle_pause", ());
                    }
                }
                "quit" => {
                    std::process::exit(0);
                }
                _ => {}
            },
            SystemTrayEvent::LeftClick { .. } => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            submit_plan,
            get_current_state,
            get_stats,
            update_category,
            pause_monitoring,
            train_models,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
