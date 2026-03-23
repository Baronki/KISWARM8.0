//! Build script for KISWARM Zero-Touch Scout
//! Embeds build information into the binary for self-verification

use vergen::EmitBuilder;

fn main() {
    // Emit build information using vergen 8.x API
    // - VERGEN_BUILD_TIMESTAMP: When the binary was built
    // - VERGEN_GIT_SHA: Git commit hash
    // - VERGEN_GIT_BRANCH: Git branch name
    
    EmitBuilder::builder()
        .build_timestamp()
        .git_sha(true)
        .git_branch()
        .emit()
        .expect("Failed to emit build information");
    
    // Print build info
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=Cargo.toml");
}
