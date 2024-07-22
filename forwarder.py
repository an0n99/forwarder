import re
import asyncio
from telethon import TelegramClient, events
from collections import defaultdict
import os


def extract_contract_address(message_text):
    match = re.search(r'[a-zA-Z0-9]{30,50}', message_text)
    if match:
        return match.group(0)
    return None


def extract_liquidity_percentage(message_text):
    match = re.search(r'💧.*\(([\d.]+)% MC\)', message_text)
    if match:
        return float(match.group(1))
    return None


def extract_price_change(message_text):
    match = re.search(r'24H: (🔴|🟢) ([\d,.]+)%', message_text)
    if match:
        direction = match.group(1)
        percentage_str = match.group(2)
        percentage_str = percentage_str.replace(',', '')  # Remove commas from the number string
        percentage = float(percentage_str)  # Convert to float
        return (direction, percentage)
    return None


def extract_volume(message_text):
    match = re.search(r'24H: \$([\d,.]+[KMB]?)', message_text)
    if match:
        volume_str = match.group(1)
        volume_str = volume_str.replace(',', '')  # Remove commas from the number string
        multiplier = 1
        if volume_str[-1] == 'K':
            multiplier = 1e3
        elif volume_str[-1] == 'M':
            multiplier = 1e6
        elif volume_str[-1] == 'B':
            multiplier = 1e9
        volume = float(volume_str[:-1]) * multiplier if multiplier != 1 else float(volume_str)
        return volume
    return None


def extract_5min_volume(message_text):
    match = re.search(r'5M: \$([\d,.]+[KMB]?)', message_text)
    if match:
        volume_str = match.group(1)
        volume_str = volume_str.replace(',', '')  # Remove commas from the number string
        multiplier = 1
        if volume_str[-1] == 'K':
            multiplier = 1e3
        elif volume_str[-1] == 'M':
            multiplier = 1e6
        elif volume_str[-1] == 'B':
            multiplier = 1e9
        volume = float(volume_str[:-1]) * multiplier if multiplier != 1 else float(volume_str)
        return volume
    return None


def check_red_alert_conditions(message_text):
    red_alert_positions = [m.start() for m in re.finditer('🚨', message_text)]
    if len(red_alert_positions) == 1 and '🚨 Very Low Liquidity' in message_text:
        return True
    if len(red_alert_positions) > 1:
        return False
    return True


async def main():
   
    api_id = 
    api_hash = ''
    phone_number = '+'

    
    client = TelegramClient('session_name', api_id, api_hash)
    contract_occurrences = defaultdict(int)

    
    file_path = '/home/ubuntu/data.txt'

    
    await client.start(phone=phone_number)

    source_chat_id = -4176617654  # Source chat ID
    destination_channel_username = '@soul_scanner_bot'  # Has to be soul_scanner_bot
    backup_channel_id = -4235593004  # Backup channel ID or Buying Bot

    
    bot_user = await client.get_me()
    bot_user_id = bot_user.id

    
    forwarded_addresses = set()

    @client.on(events.NewMessage(chats=destination_channel_username))
    async def reply_handler(event):
        if event.is_reply:
            original_message = await event.get_reply_message()
            if original_message.sender_id == bot_user_id:
                print(f"Reply message in destination chat: {event.text}")

               
                if "🚨 0% Burnt" in event.raw_text:
                    print("Message contains '🚨 0% Burnt', skipping backup forwarding.")
                    return

                if "Burnt" not in event.raw_text:
                    print("Message does not contain 'Burnt', skipping backup forwarding.")
                    return

                if not check_red_alert_conditions(event.raw_text):
                    print("Message contains invalid 🚨 emoji conditions, skipping backup forwarding.")
                    return

                if "High Individual Holder" in event.raw_text:
                    print("Message contains 'High Individual Holder', skipping backup forwarding.")
                    return

                if "High Top Ten Holding" in event.raw_text:
                    print("Message contains 'High Top Ten Holding', skipping backup forwarding.")
                    return

                airdrop_match = re.search(r'Airdrops: \d+% 🚨', event.raw_text)
                if airdrop_match:
                    print("Message contains 'Airdrops: <percentage>% 🚨', skipping backup forwarding.")
                    return

               
                liquidity_percentage = extract_liquidity_percentage(event.text)
                if liquidity_percentage is not None and liquidity_percentage > 7:
                    try:
                        
                        await client.send_message(backup_channel_id, original_message.text)
                        print(f"Contract address {original_message.text} sent to backup channel.")

                        
                        forwarded_addresses.add(original_message.text)

                        
                        contract_address = extract_contract_address(original_message.text)
                        if contract_address:
                            contract_occurrences[contract_address] = 0
                            print(f"Reset occurrence count for contract address {contract_address}")

                    except Exception as e:
                        print(f"Error sending message to backup channel: {e}")

    @client.on(events.NewMessage(chats=source_chat_id))
    async def handler(event):
        if "is now trending" in event.raw_text:
            print(f"Message received in source chat: {event.raw_text}")

            contract_address = extract_contract_address(event.raw_text)
            if contract_address:
                print(f"Extracted contract address: {contract_address}")

                
                if contract_address in contract_occurrences:
                    print(f"Contract address {contract_address} already forwarded, skipping.")
                    return

                volume_5min = extract_5min_volume(event.raw_text)
                if volume_5min:
                    print(f"5M Volume: ${volume_5min}")

                   
                    if volume_5min < 1000:
                        print("Volume is lower than $1K, skipping forwarding.")
                        return

                    try:
                        print(f"Attempting to forward contract address {contract_address} to destination channel.")
                        await client.send_message(destination_channel_username, contract_address)
                        print(f"Contract address {contract_address} forwarded to destination channel successfully.")

                        
                        try:
                            with open(file_path, 'a') as file:
                                file.write(event.raw_text.replace('\n', ' ') + '\n')
                                print(f"Original message saved to file.")
                        except Exception as e:
                            print(f"Error writing original message to file: {e}")

                        # Mark this contract address as forwarded
                        contract_occurrences[contract_address] = True

                    except Exception as e:
                        print(f"Error sending message to destination channel: {e}")
                else:
                    print("No valid 5M volume found in the message.")

    print("Listening for new messages in the source chat...")
    await client.run_until_disconnected()

asyncio.run(main())
