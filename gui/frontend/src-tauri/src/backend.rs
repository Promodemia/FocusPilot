use anyhow::Result;

pub async fn check_backend() -> Result<bool> {
    if let Ok(response) = reqwest::Client::new()
        .get("http://localhost:8765/health")
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await
    {
        Ok(response.status().is_success())
    } else {
        Ok(false)
    }
}

pub fn start_python_backend() -> Result<()> {
    // Start backend from the gui/backend directory
    let backend_path = if cfg!(windows) {
        "..\\backend\\main.py"
    } else {
        "../backend/main.py"
    };

    std::process::Command::new(if cfg!(windows) { "python" } else { "python3" })
        .arg(backend_path)
        .current_dir("..")
        .spawn()?;

    Ok(())
}
