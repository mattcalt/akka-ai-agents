import emoji

def process_message(input_message):
    return emoji.emojize(f"Python processed: {input_message} :thumbs_up:", language='alias') 