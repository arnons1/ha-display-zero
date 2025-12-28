#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
from PIL import Image, ImageFont, ImageDraw
from inky.auto import auto
from datetime import datetime
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

HEADERS = {"Authorization": f"Bearer {HA_TOKEN}"}

FONT_MAIN = "./DejaVuSans-Bold.ttf"
FONT_ICONS = "./fa-solid-900.ttf"

def get_ha_data(entity_id):
    try:
        r = requests.get(HA_URL + entity_id, headers=HEADERS)
        return r.json()
    except:
        return {"state": "Error"}

def get_relative_time(start_str):
    """Calculates hours/minutes until the event."""
    try:
        # HA date format: 2026-01-04 11:30:00
        start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        diff = start_dt - now
        
        if diff.total_seconds() < 0:
            return "Started"
        
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        if days > 0:
            return f"In {days}d {hours}h"
        if hours > 0:
            return f"In {hours}h {minutes}m"
        return f"In {minutes}m"
    except:
        return "Time Error"

def draw_page_1(draw, inky):
    """Home Status Page"""
    # Fetch Data
    open_count_raw = get_ha_data("number.open_doors_and_windows")['state']
    # Convert to int safely
    open_count = int(float(open_count_raw)) if open_count_raw != "Error" else 0
    last_open = get_ha_data("sensor.kitchen_door_last_opened_human")['state']
    alarm = get_ha_data("alarm_control_panel.master")['state']

    # 2. Refined Font Sizes
    font_main = ImageFont.truetype(FONT_MAIN, 16)       # Headers
    font_sub = ImageFont.truetype(FONT_MAIN, 12)        # Descriptions
    font_tiny = ImageFont.truetype(FONT_MAIN, 8)        # Small metadata/labels
    font_icons = ImageFont.truetype(FONT_ICONS, 18)     # Scaled icons
    
    # 3. Windows/Doors Section
    win_color = inky.RED if open_count > 0 else inky.BLACK
    draw.text((10, 12), "\uf2d0", win_color, font=font_icons)
    draw.text((40, 12), f"{open_count} Openings", win_color, font=font_main)
    
    # 4. Kitchen Door Section (39, 37, 45)
    # COLOR LOGIC: If 'hours' is in string and the number is >= 3
    # or if 'day' is in the string.
    door_color = inky.BLACK
    time_parts = last_open.split() # Splits "27 minutes ago" -> ['27', 'minutes', 'ago']
    
    try:
        if "hour" in last_open:
            # Check if it's 3, 4, etc. (Since 2.5h is usually represented as 3h)
            hours_val = float(time_parts[0])
            if hours_val >= 2.5:
                door_color = inky.RED
        elif "day" in last_open:
            door_color = inky.RED
    except:
        door_color = inky.BLACK

    draw.text((12, 39), "\uf6d3", door_color, font=font_icons)
    draw.text((33, 37), "KITCHEN DOOR", door_color, font=font_tiny)
    draw.text((32, 45), f"Opened {last_open}", door_color, font=font_sub)
    
    # 5. Alarm Section
    alarm_icon = "\uf3ed" if alarm == "disarmed" else "\uf023"
    alarm_color = inky.BLACK if alarm == "disarmed" else inky.RED
    draw.text((12, 66), alarm_icon, alarm_color, font=font_icons)
    draw.text((40, 66), f"ALARM: {alarm}", alarm_color, font=font_main)

def draw_page_2(draw, inky):
    """Calendar Page"""
    cal_data = get_ha_data("calendar.arnon_shimoni_gmail_com")
    attrs = cal_data.get('attributes', {})
    
    message = attrs.get('message', 'No Meetings')
    is_all_day = attrs.get('all_day', False)
    start_time_raw = attrs.get('start_time', '')
    
    # Fonts
    font_tiny = ImageFont.truetype(FONT_MAIN, 11)    # For Label
    font_msg = ImageFont.truetype(FONT_MAIN, 15)     # Slightly under max to ensure fit
    font_time = ImageFont.truetype(FONT_MAIN, 12)   # For Countdown
    font_icons = ImageFont.truetype(FONT_ICONS, 14)  # Smaller icons to save space

    # 1. Header Area (Y: 10-22)
    # We move the icon and "NEXT EVENT" onto the same line to save height
    draw.text((10, 10), "\uf073", inky.RED, font=font_icons)
    draw.text((32, 12), "NEXT EVENT", inky.RED, font=font_tiny)

    # 2. Message Area (Y: 28-48)
    # Truncate slightly earlier to prevent wrapping issues
    display_msg = (message[:20] + '..') if len(message) > 22 else message
    draw.text((10, 29), display_msg, inky.BLACK, font=font_msg)

    # 3. Time/Status Area (Y: 52-70)
    if is_all_day:
        draw.text((12, 53), "\uf783", inky.BLACK, font=font_icons)
        draw.text((32, 53), "All Day Event", inky.BLACK, font=font_time)
    else:
        countdown_text = get_relative_time(start_time_raw)
        # Change color to RED if event is in less than 15 minutes
        time_color = inky.RED if "m" in countdown_text and "h" not in countdown_text and int(countdown_text.split('m')[0].split()[-1]) < 15 else inky.BLACK
        
        draw.text((12, 53), "\uf252", time_color, font=font_icons)
        draw.text((32, 53), countdown_text, time_color, font=font_time)

def draw_footer(draw, inky):
    small_font = ImageFont.truetype(FONT_MAIN, 9)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Draw separator
    draw.line((0, inky.HEIGHT - 14, inky.WIDTH, inky.HEIGHT - 14), fill=inky.BLACK)
    
    update_text = f"Last Update: {timestamp}"
    
    # NEW PILLOW 10+ METHOD:
    # get text bounding box: (left, top, right, bottom)
    bbox = draw.textbbox((0, 0), update_text, font=small_font)
    text_width = bbox[2] - bbox[0]
    
    # Calculate right-aligned X position
    x_pos = inky.WIDTH - text_width - 5
    y_pos = inky.HEIGHT - 12
    
    draw.text((x_pos, y_pos), update_text, inky.BLACK, font=small_font)

# --- MAIN EXECUTION ---
inky = auto()
img = Image.new("P", (inky.WIDTH, inky.HEIGHT))
draw = ImageDraw.Draw(img)

# Toggle logic
try:
    with open("page_state.txt", "r") as f:
        current_page = int(f.read())
except:
    current_page = 1

if current_page == 1:
    draw_page_1(draw, inky)
    draw_footer(draw, inky)
    next_page = 2
else:
    draw_page_2(draw, inky)
    draw_footer(draw, inky)
    next_page = 1

with open("page_state.txt", "w") as f:
    f.write(str(next_page))

inky.set_image(img)
inky.show()
