use std::env;

use crate::backend::BackendConfig;

pub struct Config {
    pub api_host: String,
    pub api_port: u16,
    pub backend_url: String,
    pub preload: bool,
    pub backend: BackendConfig,
}

impl Config {
    pub fn load() -> Self {
        let api_host = env::var("API_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let api_port = env::var("API_PORT")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(7095);
        let backend_port = env::var("BACKEND_PORT")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(7105);
        let backend_url = env::var("BACKEND_URL").unwrap_or_else(|_| format!("http://localhost:{}", backend_port));
        let preload = env::var("PRELOAD")
            .ok()
            .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
            .unwrap_or(true);
        let backend = BackendConfig::from_env(backend_port);
        Self {
            api_host,
            api_port,
            backend_url,
            preload,
            backend,
        }
    }
}
