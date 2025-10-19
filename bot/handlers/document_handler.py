from telegram import Update
from telegram.ext import MessageHandler, CallbackContext, filters
import logging
import tempfile
import os
from bot.services.document_parser import document_parser
from bot.services.translation import translation_service
from bot.services.database import db_manager
from bot.utils.helpers import format_translation_result, truncate_text

logger = logging.getLogger(__name__)

async def handle_document(update: Update, context: CallbackContext):
    """Handle document uploads for translation - NO LIMITS"""
    user_id = update.effective_user.id
    document = update.message.document
    filename = document.file_name
    
    if not document_parser.is_supported_document(filename):
        await update.message.reply_text(
            "❌ Unsupported document format. Please upload PDF, DOCX, or TXT files."
        )
        return
    
    # Get user's default language
    user_prefs = db_manager.get_user_preferences(user_id)
    target_lang = user_prefs.get('default_language', 'en')
    
    if not target_lang:
        await update.message.reply_text("Please set your default language first using /setlang command.")
        return
    
    temp_path = None
    processing_msg = None
    
    try:
        # Download document
        document_file = await document.get_file()
        
        # Create temporary file with explicit cleanup
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_path = temp_file.name
            await document_file.download_to_drive(temp_path)
        
        # Extract text from document
        extracted_text, word_count = document_parser.extract_text(temp_path, filename)
        
        if not extracted_text:
            await update.message.reply_text("❌ Could not extract text from the document.")
            return
        
        # NO WORD COUNT LIMIT - Process documents of any size
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"📄 Processing document ({word_count:,} words)..."
        )
        
        # Check text length for translation service limits
        if len(extracted_text) > 4500:  # Leave some buffer for API limits
            # Split text into chunks for translation
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=f"📄 Large document detected ({word_count:,} words). Processing in chunks..."
            )
            
            # Split text into chunks of 4000 characters
            chunks = []
            current_chunk = ""
            
            for paragraph in extracted_text.split('\n'):
                if len(current_chunk) + len(paragraph) + 1 < 4000:
                    current_chunk += paragraph + '\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n'
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Translate each chunk
            translated_chunks = []
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                if len(chunk) > 0:
                    try:
                        chunk_result = translation_service.translate_text(chunk, target_lang)
                        translated_chunks.append(chunk_result['translated_text'])
                        # Update progress
                        progress = f"📄 Processing chunk {i+1}/{total_chunks}..."
                        await context.bot.edit_message_text(
                            chat_id=processing_msg.chat_id,
                            message_id=processing_msg.message_id,
                            text=progress
                        )
                    except Exception as e:
                        logger.error(f"Chunk translation failed: {e}")
                        translated_chunks.append(f"[Translation failed for this section: {str(e)}]")
            
            # Combine translated chunks
            full_translated_text = '\n\n'.join(translated_chunks)
            translation_result = {
                'original_text': extracted_text,
                'translated_text': full_translated_text,
                'source_language': 'auto',
                'target_language': target_lang
            }
        else:
            # Normal translation for smaller documents
            translation_result = translation_service.translate_text(extracted_text, target_lang)
        
        # Save to history (truncated for storage)
        history_data = translation_result.copy()
        history_data['original_text'] = truncate_text(extracted_text, 200)
        history_data['translated_text'] = truncate_text(translation_result['translated_text'], 200)
        history_data['translation_type'] = 'document'
        db_manager.add_translation_history(user_id, history_data)
        
        # Prepare response
        response = f"📄 **Document Translation**\n\n"
        response += f"**File:** {filename}\n"
        response += f"**Words:** {word_count:,}\n\n"
        response += format_translation_result(translation_result)
        
        # Send as text if not too long, otherwise as file
        if len(response) < 4000:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=response,
                parse_mode='Markdown'
            )
        else:
            # Send truncated message and full translation as file
            truncated_response = f"📄 **Document Translation**\n\n**File:** {filename}\n**Words:** {word_count:,}\n\nTranslation completed! Sending as file..."
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=truncated_response,
                parse_mode='Markdown'
            )
            
            # Send translated text as file
            output_temp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                    output_temp_path = f.name
                    f.write(translation_result['translated_text'])
                
                with open(output_temp_path, 'rb') as doc_file:
                    await update.message.reply_document(
                        document=doc_file,
                        filename=f"translated_{os.path.splitext(filename)[0]}.txt",
                        caption=f"📄 Translated document ({word_count:,} words)"
                    )
                
            finally:
                # Cleanup output temporary file
                if output_temp_path and os.path.exists(output_temp_path):
                    try:
                        os.unlink(output_temp_path)
                    except Exception as e:
                        logger.warning(f"Could not cleanup output temp file: {e}")
            
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        error_msg = f"❌ Document processing failed: {str(e)}"
        if processing_msg:
            try:
                await context.bot.edit_message_text(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id,
                    text=error_msg
                )
            except:
                await update.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
    
    finally:
        # Cleanup temporary file in finally block to ensure it runs
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Could not cleanup temp file {temp_path}: {e}")

def setup_handlers(application):
    """Setup document handler"""
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))