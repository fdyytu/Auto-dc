# Perbaikan Error: AttributeError: 'Interaction' object has no attribute 'custom_id'

## Deskripsi Error

Error ini terjadi karena kode mencoba mengakses `interaction.custom_id` secara langsung, padahal dalam Discord.py, `custom_id` tidak tersedia sebagai atribut langsung pada objek `Interaction`.

### Error Log:
```
AttributeError: 'Interaction' object has no attribute 'custom_id'
File "/app/src/cogs/ticket/views/ticket_view.py", line 46, in create_ticket_button
logger.info(f"Create ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")
```

## Root Cause

Dalam Discord.py, `custom_id` tidak dapat diakses langsung dari objek `Interaction`. Cara yang benar untuk mengakses `custom_id` adalah:

1. **Untuk button callbacks**: Gunakan `button.custom_id` (parameter kedua dalam callback)
2. **Untuk interaction data**: Gunakan `interaction.data.get('custom_id')`
3. **Untuk modal submissions**: Gunakan `interaction.data.get('custom_id')`

## Perbaikan yang Dilakukan

### 1. File: `src/cogs/ticket/views/ticket_view.py`

#### Sebelum:
```python
# Baris 30 - TicketView.close_ticket_callback
logger.info(f"Close ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")

# Baris 46 - TicketControlView.create_ticket_button  
logger.info(f"Create ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")

# Baris 60 - TicketConfirmView.confirm_button
logger.info(f"Confirm ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")

# Baris 70 - TicketConfirmView.cancel_button
logger.info(f"Cancel ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")
```

#### Sesudah:
```python
# Baris 30 - TicketView.close_ticket_callback
custom_id = interaction.data.get('custom_id', 'unknown')
logger.info(f"Close ticket button clicked by {interaction.user} (custom_id: {custom_id})")

# Baris 46 - TicketControlView.create_ticket_button  
logger.info(f"Create ticket button clicked by {interaction.user} (custom_id: {button.custom_id})")

# Baris 60 - TicketConfirmView.confirm_button
logger.info(f"Confirm ticket button clicked by {interaction.user} (custom_id: {button.custom_id})")

# Baris 70 - TicketConfirmView.cancel_button
logger.info(f"Cancel ticket button clicked by {interaction.user} (custom_id: {button.custom_id})")
```

### 2. File: `src/cogs/ticket/ticket_cog.py`

#### Sebelum:
```python
# Baris 423 - on_modal_submit
if not getattr(interaction, 'custom_id', None) or interaction.custom_id != "create_ticket":
    logger.warning(f"Modal submit dari {interaction.user} memiliki custom_id tidak valid")
```

#### Sesudah:
```python
# Baris 423 - on_modal_submit
modal_custom_id = interaction.data.get('custom_id')
if not modal_custom_id or modal_custom_id != "create_ticket":
    logger.warning(f"Modal submit dari {interaction.user} memiliki custom_id tidak valid: {modal_custom_id}")
```

## Penjelasan Perbaikan

### 1. Button Callbacks dengan Parameter Button
Untuk callback button yang memiliki parameter `button`, gunakan `button.custom_id`:
```python
async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
    custom_id = button.custom_id  # ✅ Benar
    # custom_id = interaction.custom_id  # ❌ Salah
```

### 2. Callback Tanpa Parameter Button
Untuk callback yang tidak memiliki parameter button, gunakan `interaction.data.get('custom_id')`:
```python
async def callback(self, interaction: discord.Interaction):
    custom_id = interaction.data.get('custom_id', 'unknown')  # ✅ Benar
    # custom_id = interaction.custom_id  # ❌ Salah
```

### 3. Modal Submissions
Untuk modal submissions, selalu gunakan `interaction.data.get('custom_id')`:
```python
async def on_modal_submit(self, interaction: discord.Interaction):
    modal_custom_id = interaction.data.get('custom_id')  # ✅ Benar
    # modal_custom_id = interaction.custom_id  # ❌ Salah
```

## Testing

Setelah perbaikan ini, error `AttributeError: 'Interaction' object has no attribute 'custom_id'` tidak akan muncul lagi. Semua logging akan berfungsi dengan baik dan menampilkan `custom_id` yang benar.

## Best Practices

1. **Selalu gunakan `button.custom_id`** jika callback memiliki parameter button
2. **Gunakan `interaction.data.get('custom_id')`** untuk akses langsung dari interaction data
3. **Tambahkan fallback value** saat menggunakan `.get()` untuk menghindari None
4. **Konsisten dalam penggunaan** metode akses custom_id di seluruh aplikasi

## Files Modified

- `src/cogs/ticket/views/ticket_view.py` - Perbaikan 4 callback functions
- `src/cogs/ticket/ticket_cog.py` - Perbaikan 1 modal submission handler

Perbaikan ini memastikan sistem ticket berfungsi dengan baik tanpa error AttributeError.
