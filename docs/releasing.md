# Publish this beta on GitHub

Suggested repository: **SNote-Video**  
Tag: **v0.1.0-beta.1**  
Release title: **SNote Video v0.1.0-beta.1 — Video subtitles**

1. Upload the extracted project source to your repository and commit it.
2. Open the repository's **Releases** page and choose **Draft a new release**.
3. Enter v0.1.0-beta.1 as a new tag, targeting the commit containing this video edition.
4. Use the title above and paste the contents of RELEASE_NOTES.md into the description.
5. Attach **SNote-Video-v0.1.0-beta.1-source.zip** as a release asset.
6. Select **Set as a pre-release**, then publish when you are ready.

On a phone, use the browser in Desktop site mode if necessary. Choose the ZIP using the release asset file picker; there is no need to select folders for the release asset. This is separate from uploading source folders to the repository.

The source ZIP contains the app, launch scripts, requirements, tests, README, and release notes. It does not bundle Python, FFmpeg, installed dependencies, or models.

## Rebuild the asset

~~~sh
python tools/package_release.py
~~~

This produces the ZIP and SHA-256 text file in dist/. The packaging script uses an explicit source-file allowlist, excluding recordings, local environments, and models. You can attach the checksum file too if you rebuild the asset yourself.

Do not describe this source asset as a portable Windows EXE. A compiled executable would require a separate packaging and operating-system testing step.

GitHub's official [release guide](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) describes tags, notes, assets, and pre-releases.
