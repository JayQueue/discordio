# Views Directory

Discord UI components (views, buttons, selects, modals) for interactive functionality.

## Overview

Views provide interactive UI elements in Discord messages using discord.py's UI framework. They handle user interactions like button clicks, dropdown selections, and modal submissions.

## Available Views

### 🔍 search_views.py

**Purpose:** Interactive UI for search results and library additions

**Classes:**
- `AddToLibraryView` - Movie/series selection with Add/Cancel buttons

---

#### AddToLibraryView

Interactive view for adding search results to Stremio library.

**Features:**
- Movie/series selection dropdown
- Add to library button
- Cancel button
- Automatic cleanup on action

**Usage:**
```python
from views.search_views import AddToLibraryView

view = AddToLibraryView(results, auth_key, media_type)
await ctx.send("Select an item:", view=view, ephemeral=True)
```

**Constructor:**
```python
def __init__(self, results: list, auth_key: str, media_type: str):
    """
    Args:
        results: List of search result dicts with 'title' and 'id' keys
        auth_key: User's Stremio authentication key
        media_type: 'movie' or 'series'
    """
```

**Components:**
1. **Dropdown Select** - Choose from search results
   - Label: "Select a {movie/series}..."
   - Options: Up to 25 results (Discord limit)
   - Each option shows title

2. **Add Button** - Add selected item to library
   - Label: "📚 Add to Library"
   - Style: Primary (blue)
   - Action: POST to Stremio API
   - Response: Success confirmation (ephemeral)

3. **Cancel Button** - Dismiss without action
   - Label: "Cancel"
   - Style: Secondary (gray)
   - Action: Send "Cancelled" message and close view

**Example Flow:**
```
User: !film inception
Bot: Shows 5 results in dropdown
User: Selects "Inception (2010)"
User: Clicks "Add to Library"
Bot: "✅ Added Inception to your library!"
View: Closes automatically
```

**Error Handling:**
- Invalid selection: Disabled until selection made
- API failure: Shows error message
- Timeout: View auto-disables after 180 seconds

---

### 📚 library_views.py

**Purpose:** Library browsing and sharing interface

**Classes:**
- `ShareItemView` - Share library item to channel or DM
- `LibraryPaginationView` - Navigate library pages with share buttons

---

#### ShareItemView

Interactive view for sharing library items.

**Features:**
- Channel selector dropdown
- User selector dropdown (DM)
- Share button (enabled after selection)
- Cancel button
- Poster display in shared message

**Usage:**
```python
from views.library_views import ShareItemView

view = ShareItemView(item, bot, interaction)
await interaction.response.send_message(
    "Choose where to share:",
    view=view,
    ephemeral=True
)
```

**Constructor:**
```python
def __init__(self, item: dict, bot, interaction: discord.Interaction):
    """
    Args:
        item: Library item dict with name, type, id, state, etc.
        bot: Bot instance
        interaction: Original interaction (for guild/user context)
    """
```

**Components:**

1. **Channel Selector** - Choose channel to share to
   - Placeholder: "Select a channel to share to..."
   - Options: All channels user can send messages to
   - Max 25 channels (Discord limit)
   - Format: "#channel-name"

2. **User Selector** - Choose user to DM
   - Placeholder: "Or select a user to DM..."
   - Options: All non-bot members except sender
   - Max 25 users (Discord limit)
   - Shows display names

3. **Share Button** - Send to selected destination
   - Label: "📤 Share"
   - Style: Primary (blue)
   - Initially disabled
   - Enabled when channel OR user selected
   - Action: Creates embed and sends

4. **Cancel Button** - Close without sharing
   - Label: "Cancel"
   - Style: Secondary (gray)

**Shared Message Format:**
```
Embed:
  Title: {emoji} {name} ({year})
  Description:
    Type: {Movie/Series}
    Status: {Watched/Not Watched}
    ID: {stremio_id}
  Thumbnail: Poster image
  Footer: "Shared by {username}"
  Color: Green (watched) or Blue (not watched)
```

**Example Flow:**
```
User: In library view, clicks "📤 Inception"
Bot: Shows share menu (ephemeral)
User: Selects "#movies" from channel dropdown
User: Clicks "Share" button
Bot: Posts embed to #movies channel
Bot: "✅ Shared to #movies!" (ephemeral confirmation)
View: Closes
```

**Permissions:**
- Requires bot to have Send Messages in target channel
- Requires Server Members Intent for DM functionality
- User must have Send Messages permission in channel

**Error Handling:**
```python
try:
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Shared!", ephemeral=True)
except discord.Forbidden:
    await interaction.response.send_message("❌ No permission!", ephemeral=True)
except Exception as e:
    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
```

---

#### LibraryPaginationView

Pagination controls for library browsing with per-item share buttons.

**Features:**
- Previous/Next navigation buttons
- Dynamic share buttons per item
- Grid view: Single share button for current item
- Table view: Share button for each item (up to 5)
- Auto-updating buttons on page change

**Usage:**
```python
from views.library_views import LibraryPaginationView

view = LibraryPaginationView(
    embeds=embeds,
    items=items,
    bot=bot,
    is_table=True,
    items_per_page=5
)
await ctx.send(embed=embeds[0], view=view, ephemeral=True)
```

**Constructor:**
```python
def __init__(self,
             embeds: list,
             items: list,
             bot,
             is_table: bool = False,
             items_per_page: int = 1):
    """
    Args:
        embeds: List of Discord embeds (one per page)
        items: List of library item dicts
        bot: Bot instance
        is_table: True for table view, False for grid view
        items_per_page: Items shown per page
    """
```

**Components:**

**Navigation Buttons:**

1. **Previous Button**
   - Label: "⬅️ Previous" (translated via `t()`)
   - Style: Secondary (gray)
   - Disabled on first page
   - Action: Show previous page

2. **Next Button**
   - Label: "➡️ Next" (translated via `t()`)
   - Style: Secondary (gray)
   - Disabled on last page
   - Action: Show next page

**Share Buttons (Grid View):**

Single button for current item:
- Label: "📤 Share Current Item"
- Style: Success (green)
- Action: Open ShareItemView for current item

**Share Buttons (Table View):**

One button per item on page (up to 5):
- Label: "📤 {item_name}" (truncated to 20 chars)
- Style: Success (green)
- Action: Open ShareItemView for specific item
- Updates when navigating pages

**Button Update Logic:**
```python
def _update_share_buttons(self):
    # Remove old share buttons
    for btn in self.share_buttons:
        self.remove_item(btn)
    self.share_buttons.clear()

    if self.is_table:
        # Add button for each item on page
        for i, item in enumerate(page_items):
            btn = create_share_button(item)
            self.add_item(btn)
            self.share_buttons.append(btn)
    else:
        # Add single button for current item
        btn = create_share_button(current_item)
        self.add_item(btn)
        self.share_buttons.append(btn)
```

**Example Flow (Grid View):**
```
Page 1: [Previous] [Next] [Share Current Item]
User: Clicks "Next"
Page 2: [Previous] [Next] [Share Current Item]
User: Clicks "Share Current Item"
Bot: Opens ShareItemView for item on page 2
```

**Example Flow (Table View):**
```
Page 1 (5 items):
  [Previous] [Next]
  [📤 Movie 1] [📤 Movie 2] [📤 Movie 3] [📤 Movie 4] [📤 Movie 5]

User: Clicks "📤 Movie 3"
Bot: Opens ShareItemView for Movie 3
```

**Timeout:**
- Views auto-disable after 180 seconds (3 minutes)
- User sees "Interaction failed" if attempting to use after timeout

---

## View Architecture

### Component Hierarchy

```
discord.ui.View (base class)
    │
    ├── AddToLibraryView
    │   ├── Select (dropdown)
    │   ├── Button (Add)
    │   └── Button (Cancel)
    │
    ├── ShareItemView
    │   ├── Select (channels)
    │   ├── Select (users)
    │   ├── Button (Share)
    │   └── Button (Cancel)
    │
    └── LibraryPaginationView
        ├── Button (Previous)
        ├── Button (Next)
        └── Button[] (Share buttons - dynamic)
```

### Callback Pattern

All interactive components use callbacks:

```python
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

        # Create button
        self.my_button = discord.ui.Button(
            label="Click Me",
            style=discord.ButtonStyle.primary
        )
        # Assign callback
        self.my_button.callback = self._button_callback
        # Add to view
        self.add_item(self.my_button)

    async def _button_callback(self, interaction: discord.Interaction):
        """Handle button click."""
        await interaction.response.send_message("Clicked!", ephemeral=True)
        self.stop()  # Close view
```

### Interaction Response

Always respond to interactions:

```python
# Edit the original message
await interaction.response.edit_message(content="Updated!", view=self)

# Send new ephemeral message
await interaction.response.send_message("Done!", ephemeral=True)

# Defer for longer operations
await interaction.response.defer(ephemeral=True)
# ... do work ...
await interaction.followup.send("Complete!")
```

---

## Creating Custom Views

### Basic Template

```python
import discord
from discord import ui
from utils.language import t

class MyCustomView(ui.View):
    """Description of view purpose."""

    def __init__(self, data: dict):
        super().__init__(timeout=180)
        self.data = data

        # Create components
        self._create_components()

    def _create_components(self):
        """Create and add UI components."""
        # Button
        self.action_btn = ui.Button(
            label=t('BUTTON_ACTION'),
            style=discord.ButtonStyle.primary
        )
        self.action_btn.callback = self._on_action
        self.add_item(self.action_btn)

        # Select
        options = [
            discord.SelectOption(label="Option 1", value="1"),
            discord.SelectOption(label="Option 2", value="2")
        ]
        self.select = ui.Select(
            placeholder=t('SELECT_PLACEHOLDER'),
            options=options
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_action(self, interaction: discord.Interaction):
        """Handle button click."""
        await interaction.response.send_message(
            t('ACTION_COMPLETE'),
            ephemeral=True
        )
        self.stop()

    async def _on_select(self, interaction: discord.Interaction):
        """Handle selection."""
        selected = self.select.values[0]
        await interaction.response.edit_message(
            content=f"Selected: {selected}",
            view=self
        )
```

### Usage in Cog

```python
from views.my_custom_view import MyCustomView

class MyCog(commands.Cog):
    @commands.command()
    async def mycommand(self, ctx):
        data = {"foo": "bar"}
        view = MyCustomView(data)

        await ctx.send(
            "Choose an option:",
            view=view,
            ephemeral=True
        )
```

---

## Best Practices

### Do's ✅

1. **Always set timeout**
   ```python
   super().__init__(timeout=180)  # 3 minutes
   ```

2. **Use ephemeral messages for views**
   ```python
   await ctx.send("Menu", view=view, ephemeral=True)
   ```

3. **Respond to all interactions**
   ```python
   await interaction.response.send_message("OK", ephemeral=True)
   ```

4. **Stop view when done**
   ```python
   self.stop()  # Prevents further interactions
   ```

5. **Handle errors gracefully**
   ```python
   try:
       await do_something()
   except Exception as e:
       await interaction.response.send_message(
           "Error occurred",
           ephemeral=True
       )
   ```

6. **Translate all text**
   ```python
   label=t('BUTTON_LABEL')  # Not "Click Here"
   ```

7. **Limit options to 25**
   ```python
   options = options[:25]  # Discord limit
   ```

### Don'ts ❌

1. **Don't forget to respond**
   ```python
   # Bad - no response
   async def callback(self, interaction):
       self.data = interaction.values[0]

   # Good - always respond
   async def callback(self, interaction):
       self.data = interaction.values[0]
       await interaction.response.defer()
   ```

2. **Don't use long timeouts**
   ```python
   # Bad
   super().__init__(timeout=3600)  # 1 hour

   # Good
   super().__init__(timeout=180)  # 3 minutes
   ```

3. **Don't block the callback**
   ```python
   # Bad
   async def callback(self, interaction):
       time.sleep(5)  # Blocks
       await interaction.response.send_message("Done")

   # Good
   async def callback(self, interaction):
       await interaction.response.defer()
       await asyncio.sleep(5)  # Async
       await interaction.followup.send("Done")
   ```

4. **Don't send non-ephemeral views**
   ```python
   # Bad (clutters channel)
   await ctx.send("Menu", view=view)

   # Good (private to user)
   await ctx.send("Menu", view=view, ephemeral=True)
   ```

---

## UI Component Types

### Buttons

```python
button = discord.ui.Button(
    label="Click Me",
    style=discord.ButtonStyle.primary,  # blue, green, gray, red, link
    custom_id="my_button",
    emoji="👍",
    disabled=False
)
button.callback = self._button_callback
self.add_item(button)
```

**Styles:**
- `primary` - Blue (blurple)
- `secondary` - Gray
- `success` - Green
- `danger` - Red
- `link` - URL button (requires `url` parameter)

### Select Dropdowns

```python
options = [
    discord.SelectOption(
        label="Option 1",
        value="opt1",
        description="First option",
        emoji="1️⃣"
    ),
    discord.SelectOption(
        label="Option 2",
        value="opt2"
    )
]

select = discord.ui.Select(
    placeholder="Choose an option...",
    options=options,
    min_values=1,
    max_values=1,
    custom_id="my_select"
)
select.callback = self._select_callback
self.add_item(select)
```

**Accessing selection:**
```python
async def _select_callback(self, interaction):
    selected_value = self.select.values[0]
    # or for multi-select
    selected_values = self.select.values  # list
```

### Text Input (Modals)

For multi-line or complex input, use modals:

```python
class MyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Input Form")

        self.text_input = discord.ui.TextInput(
            label="Enter text",
            placeholder="Type here...",
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.text_input.value
        await interaction.response.send_message(
            f"You entered: {value}",
            ephemeral=True
        )

# Show modal
modal = MyModal()
await interaction.response.send_modal(modal)
```

---

## Testing Views

### Manual Testing

1. Start bot: `docker-compose up -d`
2. Run command that shows view
3. Test all buttons/selects
4. Verify ephemeral messages
5. Check timeout behavior
6. Test error cases

### Interaction Testing

```python
# Test button enable/disable
view = ShareItemView(item, bot, interaction)
assert view.share_btn.disabled == True  # Initially disabled

# Simulate channel selection
view.selected_channel = 123456789
view._update_buttons()
assert view.share_btn.disabled == False  # Enabled after selection
```

---

## Component Limits

Discord enforces limits per message:

| Component | Limit |
|-----------|-------|
| Action Rows | 5 per message |
| Buttons | 5 per row, 25 total |
| Selects | 1 per row, 5 total |
| Select Options | 25 per select |
| Text Inputs (Modal) | 5 per modal |

**Example:**
```
Row 1: [Btn1] [Btn2] [Btn3] [Btn4] [Btn5]
Row 2: [Select with 25 options]
Row 3: [Btn6] [Btn7]
Row 4: [Select with 10 options]
Row 5: [Btn8] [Btn9] [Btn10]

Total: 10 buttons + 2 selects = Valid ✅
```

---

## Performance

### View Lifecycle

1. **Create** - Instantiate view with components
2. **Send** - Attach to message
3. **Active** - Listen for interactions (timeout period)
4. **Interact** - Process callbacks
5. **Stop** - Explicitly stopped or timeout reached
6. **Cleanup** - Automatic garbage collection

### Memory Considerations

- Views persist in memory until stopped
- Auto-cleanup after timeout (default 180s)
- Call `view.stop()` explicitly when done
- Don't create views in loops without cleanup

---

## Dependencies

- `discord.py` - Discord UI framework
- `utils/language.py` - Translation system
- `services/tmdb.py` - Poster fetching (in ShareItemView)

---

## Future Enhancements

- [ ] Persistent views (survive bot restarts)
- [ ] View state persistence to database
- [ ] Custom emoji support
- [ ] Image button components
- [ ] Enhanced modal forms
- [ ] Multi-page modals
- [ ] View analytics (click tracking)
- [ ] A/B testing different view layouts
