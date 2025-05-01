#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events, Button
from loguru import logger
from typing import Dict, List, Optional
from datetime import datetime
import random

# Card colors
COLORS = ["🔴", "🔵", "🟡", "🟢"]
NUMBERS = list(range(10))
SPECIAL_CARDS = ["⛔️", "🔄", "+2"]
WILD_CARDS = ["🎨", "+4"]

class UnoGame:
    def __init__(self, chat_id: int, creator_id: int):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.players: List[int] = [creator_id]
        self.started = False
        self.deck: List[str] = self._create_deck()
        self.hands: Dict[int, List[str]] = {}
        self.current_card: Optional[str] = None
        self.current_player_index = 0
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.pending_draw = 0
        self.last_action_time = datetime.now()

    def _create_deck(self) -> List[str]:
        """Create a new shuffled deck of Uno cards."""
        deck = []
        
        # Add number cards (0-9) in each color
        for color in COLORS:
            deck.append(f"{color}0")  # One zero per color
            for _ in range(2):  # Two of each 1-9
                for num in range(1, 10):
                    deck.append(f"{color}{num}")
        
        # Add special cards (Skip, Reverse, +2) in each color
        for color in COLORS:
            for _ in range(2):  # Two of each special card per color
                for special in SPECIAL_CARDS:
                    deck.append(f"{color}{special}")
        
        # Add wild cards
        for _ in range(4):  # Four of each wild card
            for wild in WILD_CARDS:
                deck.append(wild)
        
        random.shuffle(deck)
        return deck

    def join_game(self, player_id: int) -> bool:
        """Add a player to the game."""
        if self.started or player_id in self.players:
            return False
        self.players.append(player_id)
        return True

    def start_game(self) -> bool:
        """Start the game and deal cards."""
        if len(self.players) < 2 or self.started:
            return False
        
        self.started = True
        
        # Deal 7 cards to each player
        for player in self.players:
            self.hands[player] = []
            for _ in range(7):
                self.hands[player].append(self.deck.pop())
        
        # Set the first card
        self.current_card = self.deck.pop()
        while self.current_card in WILD_CARDS:
            self.deck.append(self.current_card)
            random.shuffle(self.deck)
            self.current_card = self.deck.pop()
        
        return True

    def play_card(self, player_id: int, card: str) -> bool:
        """Play a card if it's valid."""
        if not self.is_valid_play(player_id, card):
            return False
        
        # Remove card from player's hand
        self.hands[player_id].remove(card)
        self.current_card = card
        
        # Handle special cards
        if "🔄" in card:  # Reverse
            self.direction *= -1
        elif "⛔️" in card:  # Skip
            self.current_player_index = (self.current_player_index + self.direction) % len(self.players)
        elif "+2" in card:  # Draw 2
            self.pending_draw += 2
        elif "+4" in card:  # Draw 4
            self.pending_draw += 4
        
        # Move to next player
        self.current_player_index = (self.current_player_index + self.direction) % len(self.players)
        self.last_action_time = datetime.now()
        
        return True

    def draw_card(self, player_id: int) -> Optional[str]:
        """Draw a card from the deck."""
        if not self.is_current_player(player_id):
            return None
        
        if not self.deck:
            # Reshuffle discarded cards
            self.deck = self._create_deck()
        
        drawn_cards = []
        cards_to_draw = max(1, self.pending_draw)
        for _ in range(cards_to_draw):
            if self.deck:
                card = self.deck.pop()
                self.hands[player_id].append(card)
                drawn_cards.append(card)
        
        self.pending_draw = 0
        self.last_action_time = datetime.now()
        
        if not self.can_play_any_card(player_id):
            self.current_player_index = (self.current_player_index + self.direction) % len(self.players)
        
        return drawn_cards

    def is_valid_play(self, player_id: int, card: str) -> bool:
        """Check if a card can be played."""
        if not self.is_current_player(player_id):
            return False
        
        if card not in self.hands[player_id]:
            return False
        
        # Wild cards can always be played
        if card in WILD_CARDS:
            return True
        
        # If there's a pending draw, only matching draw cards can be played
        if self.pending_draw > 0:
            if "+2" in self.current_card and "+2" in card:
                return True
            if "+4" in self.current_card and "+4" in card:
                return True
            return False
        
        # Check if card matches color or number/symbol
        current_color = self.current_card[0] if len(self.current_card) > 1 else None
        current_value = self.current_card[1:] if len(self.current_card) > 1 else self.current_card
        
        card_color = card[0] if len(card) > 1 else None
        card_value = card[1:] if len(card) > 1 else card
        
        return card_color == current_color or card_value == current_value

    def is_current_player(self, player_id: int) -> bool:
        """Check if it's the player's turn."""
        return self.started and self.players[self.current_player_index] == player_id

    def can_play_any_card(self, player_id: int) -> bool:
        """Check if player has any valid cards to play."""
        return any(self.is_valid_play(player_id, card) for card in self.hands[player_id])

    def get_game_state(self) -> Dict:
        """Get the current game state."""
        return {
            "chat_id": self.chat_id,
            "players": self.players,
            "started": self.started,
            "current_card": self.current_card,
            "current_player": self.players[self.current_player_index] if self.started else None,
            "direction": "➡️" if self.direction == 1 else "⬅️",
            "pending_draw": self.pending_draw,
            "hands": self.hands,
            "deck_size": len(self.deck)
        }

def register_uno_handlers(client, database, config):
    """Register Uno game handlers.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    # Store active games
    active_games: Dict[int, UnoGame] = {}
    
    @client.on(events.NewMessage(pattern=r"^[!?/]uno$"))
    async def uno_command(event):
        """Handler for the uno command to start a new game."""
        if event.is_private:
            await event.respond("Uno can only be played in groups!")
            return
        
        chat_id = event.chat_id
        user_id = event.sender_id
        
        # Check if there's already a game in this chat
        if chat_id in active_games:
            game = active_games[chat_id]
            if not game.started:
                if game.join_game(user_id):
                    buttons = [
                        [Button.inline("Start Game", data="uno_start")],
                        [Button.inline("Join Game", data="uno_join")]
                    ]
                    await event.respond(
                        f"Joined the Uno game! Current players: {len(game.players)}\n"
                        f"Waiting for more players to join...",
                        buttons=buttons
                    )
                else:
                    await event.respond("You're already in the game!")
            else:
                await event.respond("A game is already in progress!")
            return
        
        # Create new game
        game = UnoGame(chat_id, user_id)
        active_games[chat_id] = game
        
        buttons = [
            [Button.inline("Start Game", data="uno_start")],
            [Button.inline("Join Game", data="uno_join")]
        ]
        
        await event.respond(
            "Started a new game of Uno!\n"
            "Click 'Join Game' to join, or 'Start Game' when ready.",
            buttons=buttons
        )
        logger.info(f"New Uno game created in chat {chat_id} by user {user_id}")

    @client.on(events.CallbackQuery(data=lambda d: d.startswith(b"uno_")))
    async def uno_callback(event):
        """Handle Uno game button callbacks."""
        data = event.data.decode("utf-8")
        chat_id = event.chat_id
        user_id = event.sender_id
        
        if chat_id not in active_games:
            await event.answer("No active game in this chat!")
            return
        
        game = active_games[chat_id]
        
        if data == "uno_join":
            if game.started:
                await event.answer("Game has already started!")
                return
            
            if game.join_game(user_id):
                await event.answer("You joined the game!")
                await event.edit(
                    f"Current players: {len(game.players)}\n"
                    f"Waiting for more players to join...",
                    buttons=[
                        [Button.inline("Start Game", data="uno_start")],
                        [Button.inline("Join Game", data="uno_join")]
                    ]
                )
            else:
                await event.answer("You're already in the game!")
        
        elif data == "uno_start":
            if user_id != game.creator_id:
                await event.answer("Only the game creator can start the game!")
                return
            
            if len(game.players) < 2:
                await event.answer("Need at least 2 players to start!")
                return
            
            if game.start_game():
                await _send_game_state(event, game)
            else:
                await event.answer("Failed to start game!")
        
        elif data.startswith("uno_play_"):
            if not game.started:
                await event.answer("Game hasn't started yet!")
                return
            
            if not game.is_current_player(user_id):
                await event.answer("It's not your turn!")
                return
            
            card = data.split("_")[2]
            if game.play_card(user_id, card):
                if len(game.hands[user_id]) == 0:
                    # Player won!
                    await event.edit(
                        f"🎉 {(await client.get_entity(user_id)).first_name} won the game! 🎉"
                    )
                    del active_games[chat_id]
                else:
                    await _send_game_state(event, game)
            else:
                await event.answer("Invalid move!")
        
        elif data == "uno_draw":
            if not game.started:
                await event.answer("Game hasn't started yet!")
                return
            
            if not game.is_current_player(user_id):
                await event.answer("It's not your turn!")
                return
            
            drawn_cards = game.draw_card(user_id)
            if drawn_cards:
                await event.answer(f"You drew: {' '.join(drawn_cards)}")
                await _send_game_state(event, game)
            else:
                await event.answer("Couldn't draw card!")

    async def _send_game_state(event, game: UnoGame):
        """Send or update the game state message."""
        state = game.get_game_state()
        current_player = await client.get_entity(state["current_player"])
        
        # Build the game state message
        message = (
            f"Current card: {state['current_card']}\n"
            f"Direction: {state['direction']}\n"
            f"Current player: {current_player.first_name}\n"
            f"Cards in deck: {state['deck_size']}\n\n"
        )
        
        if state["pending_draw"] > 0:
            message += f"⚠️ Next player must draw {state['pending_draw']} cards or play a matching draw card!\n\n"
        
        # Show each player's card count
        for player_id in state["players"]:
            player = await client.get_entity(player_id)
            cards = len(state["hands"][player_id])
            message += f"{player.first_name}: {cards} cards\n"
        
        # Build buttons for current player's cards
        buttons = []
        if game.is_current_player(event.sender_id):
            hand = state["hands"][event.sender_id]
            # Group cards by color
            grouped_cards = {}
            for card in hand:
                color = card[0] if len(card) > 1 else "Special"
                if color not in grouped_cards:
                    grouped_cards[color] = []
                grouped_cards[color].append(card)
            
            # Create buttons for each color group
            for color in grouped_cards:
                row = []
                for card in grouped_cards[color]:
                    row.append(Button.inline(card, data=f"uno_play_{card}"))
                    if len(row) == 4:  # Max 4 cards per row
                        buttons.append(row)
                        row = []
                if row:
                    buttons.append(row)
            
            # Add draw button
            buttons.append([Button.inline("Draw Card 🎴", data="uno_draw")])
        
        try:
            await event.edit(message, buttons=buttons)
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
            # Try sending a new message if editing fails
            await event.respond(message, buttons=buttons)
