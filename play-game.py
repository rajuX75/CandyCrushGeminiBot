import requests
import base64
import json
import time
import traceback
from pathlib import Path
from screenshot_lib import ScreenshotConfig, ScreenshotTool
import pyautogui

class CandyCrushGeminiBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.screenshot_config = ScreenshotConfig()
        self.screenshot_tool = ScreenshotTool(self.screenshot_config)
        
    def encode_image(self, image_path):
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_with_gemini(self, image_path):
        """Analyze game state using Gemini AI with enhanced strategic planning"""
        base64_image = self.encode_image(image_path)
        
        # Enhanced strategic prompt for Gemini
        prompt = """
        Analyze this Candy Crush Saga game board as a strategic AI assistant. Think 3 moves ahead to create special candies and combinations.

        Special Candy Types to look for:
        - Striped Candy (4 in a row/column)
        - Wrapped Candy (L or T shape with 5 candies)
        - Color Bomb (5 in a row)
        - Swedish Fish (fish-shaped candy)

        For each possible move, analyze:
        1. Immediate match created
        2. Special candies that could be created
        3. Potential cascade effects
        4. Setup opportunities for next 2 moves
        5. How it advances level objectives

        Consider these priorities:
        1. Creating color bombs (highest priority)
        2. Setting up special candy combinations
        3. Creating wrapped or striped candies
        4. Moves that trigger cascades
        5. Moves that clear objectives
        
        Return your analysis in this exact JSON format:
        {
            "moves_left": number,
            "current_objectives": {
                "type": "description of what needs to be collected/cleared",
                "target": number,
                "current": number
            },
            "best_move": {
                "start_pos": [row, col],
                "direction": "up/down/left/right",
                "immediate_outcome": "what happens right after the move",
                "cascade_potential": "description of likely cascade effects",
                "next_moves": [
                    {
                        "setup": "what this sets up for next move",
                        "position": [row, col],
                        "special_candy": "type of special candy possible"
                    }
                ]
            },
            "special_candies": [
                {
                    "type": "striped/wrapped/color_bomb",
                    "position": [row, col],
                    "potential_combinations": "description of possible combinations"
                }
            ]
        }

        Think through each step carefully:
        1. Scan for any existing special candies and their positions
        2. Identify all possible matches
        3. For each match, simulate the cascade effect
        4. Look for setups that could create special candies in future moves
        5. Evaluate which move creates the best chain of events

        Focus on creating combinations of special candies when possible, as these create the most powerful effects.

        Board coordinates start from top-left (0,0) and increase going right and down.
        Ensure all positions returned are valid board coordinates.
        """

        # Prepare the request payload
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]
        }

        # Make the API request
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload
            )
            response.raise_for_status()
            
            # Parse and return the AI response
            result = response.json()
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            json_str = text_response[text_response.find('{'):text_response.rfind('}')+1]
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Error analyzing game state: {e}")
            traceback.print_exc()
            return None

    def print_analysis(self, game_state):
        """Print detailed analysis of the game state"""
        print(f"\nMoves left: {game_state['moves_left']}")
        print(f"\nObjective: {game_state['current_objectives']['type']}")
        print(f"Progress: {game_state['current_objectives']['current']}/{game_state['current_objectives']['target']}")
        
        print("\nBest Move Analysis:")
        move = game_state['best_move']
        print(f"- Position: Row {move['start_pos'][0]}, Col {move['start_pos'][1]}")
        print(f"- Direction: {move['direction']}")
        print(f"- Immediate outcome: {move['immediate_outcome']}")
        print(f"- Cascade potential: {move['cascade_potential']}")
        
        print("\nNext Move Setups:")
        for next_move in move['next_moves']:
            print(f"- {next_move['setup']}")
            print(f"  Position: Row {next_move['position'][0]}, Col {next_move['position'][1]}")
            print(f"  Potential: {next_move['special_candy']}")
        
        if game_state['special_candies']:
            print("\nSpecial Candies on Board:")
            for candy in game_state['special_candies']:
                print(f"- {candy['type']} at Row {candy['position'][0]}, Col {candy['position'][1]}")
                print(f"  Potential: {candy['potential_combinations']}")

    def make_move(self, move_info):
        """Execute the move based on AI analysis"""
        try:
            # Calculate cell size based on region
            region = self.screenshot_config.region
            board_width = region[2] - region[0]
            board_height = region[3] - region[1]
            cell_size = min(board_width, board_height) // 9  # Assuming standard 9x9 board
            
            # Get start position
            row, col = move_info['start_pos']
            start_x = region[0] + (col * cell_size) + (cell_size // 2)
            start_y = region[1] + (row * cell_size) + (cell_size // 2)
            
            # Calculate end position based on direction
            direction_map = {
                'up': (0, -1),
                'down': (0, 1),
                'left': (-1, 0),
                'right': (1, 0)
            }
            dx, dy = direction_map[move_info['direction']]
            
            end_x = start_x + (dx * cell_size)
            end_y = start_y + (dy * cell_size)
            
            # Execute move
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, duration=0.5)
            
            # Wait for animations
            time.sleep(1)
            
        except Exception as e:
            print(f"Error executing move: {e}")
            traceback.print_exc()

    def play_game(self):
        """Main game loop"""
        print("Starting Candy Crush Bot with Gemini AI...")
        print("Please select the game board area...")
        
        # Initial region selection
        self.screenshot_tool.select_region()
        
        while True:
            try:
                # Capture current game state
                image_path = self.capture_game_state()
                
                # Get Gemini AI analysis
                game_state = self.analyze_with_gemini(image_path)
                
                if not game_state:
                    print("Could not analyze game state")
                    continue
                
                # Print detailed analysis
                self.print_analysis(game_state)
                
                # Check if we should continue
                if game_state['moves_left'] <= 0:
                    print("Game finished!")
                    break
                
                # Execute best move
                self.make_move(game_state['best_move'])
                
                # Wait for animations and board updates
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\nBot stopped by user")
                break
            except Exception as e:
                print(f"Error in game loop: {e}")
                traceback.print_exc()
                break

    def capture_game_state(self):
        """Capture the current game state"""
        self.screenshot_tool.take_screenshot()
        latest_screenshot = max(Path(self.screenshot_config.save_dir).glob('*.png'))
        return latest_screenshot

if __name__ == "__main__":
    GEMINI_API_KEY = "GEMINI_API_KEY"  # Replace with your actual Gemini API key
    bot = CandyCrushGeminiBot(GEMINI_API_KEY)
    bot.play_game()