from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def quantity_keyboard(prod_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="1", callback_data=f"buyqty_{prod_id}_1"),
            InlineKeyboardButton(text="2", callback_data=f"buyqty_{prod_id}_2"),
            InlineKeyboardButton(text="3", callback_data=f"buyqty_{prod_id}_3"),
        ],
        [
            InlineKeyboardButton(text="4", callback_data=f"buyqty_{prod_id}_4"),
            InlineKeyboardButton(text="5", callback_data=f"buyqty_{prod_id}_5"),
            InlineKeyboardButton(text="10", callback_data=f"buyqty_{prod_id}_10"),
        ],
        [
            InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)