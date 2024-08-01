# Instagram Combo Checker

This project is an Instagram combo checker that validates username and password combinations. It supports proxy usage to avoid rate limiting and provides options to use your own proxies, download new proxies, or run without proxies.

## Features

- Fetch and update proxies from a specified API
- Read proxies from a file
- Verify proxy functionality
- Use valid proxies in requests to Instagram
- Handle Instagram login process and record successful logins, including those requiring verification

## Requirements

- Python 3.6+
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Download the project folder.

2. Run `setup.bat` to install the required Python packages.

3. Run `start.bat` to start the script.

## Usage

1. Ensure you have a file named `combo.txt` in the project directory with your username:password combinations, one per line.

2. Run the script by executing `start.bat`.

3. Follow the prompts to choose how you want to handle proxies:
    - Use your own proxies from `proxys.txt`
    - Download new proxies from the specified API
    - Run without proxies (use your own IP)

4. The script will check the combinations and output the results to `good.txt` for successful logins.

## Proxy Handling

- **Option 1**: Use proxies from `proxys.txt`:
  - Ensure you have a `proxys.txt` file with proxies listed, one per line.

- **Option 2**: Download and use new proxies:
  - The script will fetch proxies from a predefined API and store them in `proxys.txt`.

- **Option 3**: Use proxyless mode:
  - The script will use your current IP to check the combinations.

## Files

- `combo.txt`: Contains username:password combinations to check.
- `proxys.txt`: Contains the proxies to use (optional, if not using proxyless mode).
- `good.txt`: Contains successfully logged in username:password combinations.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Disclaimer

This script is intended solely for educational purposes. Misuse of this tool can lead to your IP being blocked by Instagram or other legal consequences. Use at your own risk. The author is not responsible for any misuse or damage caused by this tool. By using this tool, you agree to use it in compliance with all applicable laws and regulations.
