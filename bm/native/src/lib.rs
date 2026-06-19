use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use pyo3::prelude::*;

#[pyfunction]
fn parse_frontmatter(text: &str) -> HashMap<String, String> {
    let mut result = HashMap::new();
    let mut lines = text.lines();
    if lines.next().map(str::trim) != Some("---") {
        return result;
    }

    for line in lines {
        if line.trim() == "---" {
            break;
        }
        if let Some((key, value)) = line.split_once(':') {
            result.insert(
                key.trim().to_string(),
                value.trim().trim_matches(['"', '\'']).to_string(),
            );
        }
    }
    result
}

#[pyfunction]
fn path_status(path: &str) -> String {
    let path = Path::new(path);
    if fs::symlink_metadata(path)
        .map(|metadata| metadata.file_type().is_symlink())
        .unwrap_or(false)
    {
        return if path.exists() {
            "symlinked".to_string()
        } else {
            "broken".to_string()
        };
    }
    if path.exists() {
        "copied".to_string()
    } else {
        "missing".to_string()
    }
}

#[pyfunction]
fn paths_overlap(source: &str, target_parent: &str) -> bool {
    let source = canonicalize_lossy(source);
    let target_parent = canonicalize_lossy(target_parent);
    let source_parent = source.parent().unwrap_or(&source);
    target_parent.starts_with(source_parent) || source.starts_with(&target_parent)
}

fn canonicalize_lossy(path: &str) -> PathBuf {
    fs::canonicalize(path).unwrap_or_else(|_| PathBuf::from(path))
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(parse_frontmatter, module)?)?;
    module.add_function(wrap_pyfunction!(path_status, module)?)?;
    module.add_function(wrap_pyfunction!(paths_overlap, module)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_string_frontmatter() {
        let parsed = parse_frontmatter("---\nname: demo\ndescription: \"Demo skill\"\n---\nbody");
        assert_eq!(parsed.get("name"), Some(&"demo".to_string()));
        assert_eq!(parsed.get("description"), Some(&"Demo skill".to_string()));
    }
}
