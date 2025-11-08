# Lyrics Collection

This repository is a curated collection of high-quality, timed music lyrics.
The primary format for all lyrics is **Advanced SubStation Alpha (`.ass`)**,
chosen for its ability to support precise, syllable-level synchronization
and rich styling.

For broader compatibility with players and devices, all `.ass` files
are automatically converted to the standard **Lyrics (`.lrc`)** format.

## Repository Structure

- **/ass**: Contains the source-of-truth lyric files in `.ass` format.
  All contributions and edits should be made here.
- **/compiled**: Contains `.lrc` files that are automatically generated from
  the files in the `/ass` directory.
  **Do not edit files in this directory directly.**

## Usage

The `.lrc` files in the `compiled` directory are ready for use with any
compatible music player.

The conversion from `.ass` to `.lrc` is handled automatically via GitHub Actions
workflow whenever changes are pushed to the `main` branch.

## Contributing

We welcome contributions! If you would like to add new lyrics or fix
existing ones, please see our [**Contributing Guidelines**](CONTRIBUTING.md).

## License

This project is licensed under
the [Creative Commons Attribution-ShareAlike 4.0 International License](LICENSE).
