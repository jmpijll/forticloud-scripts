# FortiCloud API Scripts

A collection of Python scripts to interact with the FortiCloud API for retrieving and managing asset information.

## Prerequisites

- Python 3.8 or higher
- Git (for version control)
- FortiCloud IAM API credentials

## Setup

1. **Clone or initialize the repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API credentials:**
   - Copy `.env.example` to `.env`
   - Fill in your FortiCloud IAM API credentials in the `.env` file

## Project Structure

```
forticloud-assets/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Template for environment variables
├── .env                              # Your actual credentials (not tracked by git)
├── .gitignore                        # Git ignore rules
├── docs/
│   └── FortiCloud_API_Research.md    # API documentation and research notes
└── scripts/
    └── get_fortigate_devices.py      # Script to retrieve FortiGate/FortiWiFi devices
```

## Scripts

### get_fortigate_devices.py

Retrieves all FortiGate and FortiWiFi devices from FortiCloud and exports them to a CSV file.

**Output columns:**
- Device Name
- Serial Number
- Contract Name
- Contract Expiration Date
- Contract Status (Active/Expired)

**Usage:**
```bash
python scripts/get_fortigate_devices.py
```

**Output:**
Creates `fortigate_devices_YYYYMMDD_HHMMSS.csv` in the current directory.

## Security Notes

- Never commit your `.env` file to version control
- Keep your API credentials secure
- Rotate credentials regularly
- Review the `.gitignore` file to ensure sensitive files are excluded

## Contributing

When adding new scripts:
1. Follow the existing code structure
2. Update this README with script documentation
3. Add any new dependencies to `requirements.txt`
4. Document API endpoints in `docs/FortiCloud_API_Research.md`

## License

Internal use only.
