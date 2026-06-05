use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct PlanData {
    pub text: String,
}

#[derive(Serialize, Deserialize)]
pub struct CategoryUpdate {
    pub app: String,
    pub category: String,
}

#[tauri::command]
pub async fn submit_plan(text: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    let response = client
        .post("http://localhost:8765/plan")
        .json(&serde_json::json!({"text": text}))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        Ok("Plan saved".to_string())
    } else {
        Err("Failed to save plan".to_string())
    }
}

#[tauri::command]
pub async fn get_current_state() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    let response = client
        .get("http://localhost:8765/current_state")
        .send()
        .await
        .map_err(|e| e.to_string())?;

    response
        .json::<serde_json::Value>()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_stats() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    let response = client
        .get("http://localhost:8765/stats")
        .send()
        .await
        .map_err(|e| e.to_string())?;

    response
        .json::<serde_json::Value>()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn update_category(app: String, category: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    let response = client
        .post("http://localhost:8765/feedback")
        .json(&serde_json::json!({"action": "category_update", "category": category}))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        Ok("Category updated".to_string())
    } else {
        Err("Failed to update category".to_string())
    }
}

#[tauri::command]
pub async fn pause_monitoring(pause: bool) -> Result<String, String> {
    let client = reqwest::Client::new();
    let response = client
        .post(format!("http://localhost:8765/pause?pause={}", pause))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        Ok(format!("Monitoring {}", if pause { "paused" } else { "resumed" }))
    } else {
        Err("Failed to change monitoring state".to_string())
    }
}

#[tauri::command]
pub async fn train_models() -> Result<String, String> {
    let client = reqwest::Client::new();
    let response = client
        .post("http://localhost:8765/train")
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        Ok("Models training started".to_string())
    } else {
        Err("Failed to start training".to_string())
    }
}
