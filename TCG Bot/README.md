# TCG Bot

This project is a Discord bot designed for managing a trading card game (TCG) experience. It allows users to buy, open, and manage card packs, track their collections, and interact with other users through currency-related commands.

## Features

- **Card Packs**: Users can purchase and open card packs to collect cards.
- **Card Collection Management**: Users can view their card collections and manage duplicates.
- **Currency System**: Users can check their balances, give coins to others, and claim daily rewards.
- **Help Command**: A comprehensive help command that lists all available commands and their descriptions.

## Project Structure

```
tcg-bot
├── bot.py                # Main entry point for the Discord bot
├── cogs                  # Contains command modules (cogs)
│   ├── binder.py         # Commands for managing and viewing card collections
│   ├── currency.py       # Currency-related commands
│   ├── duplicates.py      # Commands for managing duplicate cards
│   ├── help.py           # Help command for listing available commands
│   ├── packs.py          # Commands for managing card packs
│   └── shop.py           # Commands for displaying the shop and handling purchases
├── data                  # Data storage for user and card information
│   ├── users.json        # User data and card collections
│   ├── balances.json     # User balances and currency data
│   ├── duplicates.json    # Duplicate card information
│   ├── user_packs.json   # Unopened packs tracking
│   └── cardpacks         # Directory for card pack JSON files
│       └── [pack_name].json
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd tcg-bot
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

4. Run the bot:
   ```
   python bot.py
   ```

## Usage

- Use `!shop` to view available card packs.
- Use `!buy <pack_name>` to purchase a card pack.
- Use `!op <pack_name>` to open a purchased pack.
- Use `!balance` to check your current balance.
- Use `!daily` to claim your daily reward.

For a complete list of commands, use `!tcghelp`.