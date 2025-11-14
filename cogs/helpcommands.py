import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import EMBED_COLOR

class HelpDropdown(discord.ui.Select):
    """Dropdown menu for help categories"""
    def __init__(self):
        options = [
            discord.SelectOption(
                label="🏠 Home",
                description="Return to main help menu",
                emoji="🏠",
                value="home"
            ),
            discord.SelectOption(
                label="🔄 Release Commands",
                description="Commands for managing release IDs",
                emoji="🔄",
                value="release"
            ),
            discord.SelectOption(
                label="⚡ Evolve Commands",
                description="Commands for managing evolve IDs",
                emoji="⚡",
                value="evolve"
            ),
            discord.SelectOption(
                label="📝 ID Recording",
                description="Commands for recording Pokemon IDs",
                emoji="📝",
                value="recording"
            ),
            discord.SelectOption(
                label="🔍 Quest Helper",
                description="Commands for event quest suggestions",
                emoji="🔍",
                value="quest"
            )
        ]
        super().__init__(
            placeholder="Choose a category...",
            options=options,
            custom_id="help_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        embed = self.get_embed_for_category(self.values[0])
        await interaction.response.edit_message(embed=embed, view=self.view)

    def get_embed_for_category(self, category: str) -> discord.Embed:
        """Get embed for selected category"""
        if category == "home":
            return self.get_home_embed()
        elif category == "release":
            return self.get_release_embed()
        elif category == "evolve":
            return self.get_evolve_embed()
        elif category == "recording":
            return self.get_recording_embed()
        elif category == "quest":
            return self.get_quest_embed()
        return self.get_home_embed()

    def get_home_embed(self) -> discord.Embed:
        """Main help menu embed"""
        embed = discord.Embed(
            title="📚 Help Menu",
            description=(
                "Welcome to the Pokemon Bot Helper! This bot helps you manage and automate Pokemon commands.\n\n"
                "**Available Categories:**\n\n"
                "🔄 **Release Commands** - Manage your Pokemon release list\n"
                "⚡ **Evolve Commands** - Manage your Pokemon evolve list\n"
                "📝 **ID Recording** - Record Pokemon IDs from messages\n"
                "🔍 **Quest Helper** - Get Pokemon suggestions for event quests\n\n"
                "Select a category from the dropdown below to see detailed commands!"
            ),
            color=EMBED_COLOR
        )
        embed.set_footer(text="Select a category to get started • Commands are case-insensitive")
        return embed

    def get_release_embed(self) -> discord.Embed:
        """Release commands help embed"""
        embed = discord.Embed(
            title="🔄 Release Commands",
            description="Manage your Pokemon release list with these commands:",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="📋 Panel Command",
            value=(
                "**`!releasepanel`** or **`!rp`**\n"
                "Opens an interactive panel with buttons to manage your release list. "
                "The easiest way to add, remove, view, and clear IDs!\n"
                "⏱️ Panel expires after 5 minutes."
            ),
            inline=False
        )

        embed.add_field(
            name="➕ Add IDs",
            value=(
                "**`!releaseadd <ids...>`** or **`!ra <ids...>`**\n"
                "Add Pokemon IDs to your release list.\n"
                "**Example:** `!ra 123 456 789`\n"
                "• Automatically ignores duplicate IDs\n"
                "• Add multiple IDs separated by spaces"
            ),
            inline=False
        )

        embed.add_field(
            name="➖ Remove IDs",
            value=(
                "**`!releaseremove <ids...>`** or **`!rr <ids...>`**\n"
                "Remove specific Pokemon IDs from your list.\n"
                "**Example:** `!rr 123 456`\n"
                "• Remove multiple IDs at once"
            ),
            inline=False
        )

        embed.add_field(
            name="📋 View List",
            value=(
                "**`!releaselist`** or **`!rl`**\n"
                "View all Pokemon IDs in your release list.\n"
                "• Shows 150 IDs per page\n"
                "• Use ◀ ▶ buttons to navigate pages"
            ),
            inline=False
        )

        embed.add_field(
            name="🔄 Release IDs",
            value=(
                "**`!release <count>`** or **`!r <count>`**\n"
                "Release Pokemon IDs from your list.\n"
                "**Example:** `!r 7` releases first 7 IDs\n"
                "• Also works as slash command: `/release 7`\n"
                "• Removes used IDs from your list\n"
                "• IDs are taken from the beginning of the list"
            ),
            inline=False
        )

        embed.add_field(
            name="🗑️ Clear All",
            value=(
                "**`!releaseclear`** or **`!rc`**\n"
                "Remove all IDs from your release list.\n"
                "⚠️ This action clears your entire list!"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Tip: Use the panel (!rp) for the easiest experience!")
        return embed

    def get_evolve_embed(self) -> discord.Embed:
        """Evolve commands help embed"""
        embed = discord.Embed(
            title="⚡ Evolve Commands",
            description="Manage your Pokemon evolve list with advanced use tracking:",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="📋 Panel Command",
            value=(
                "**`!evolvepanel`** or **`!ep`**\n"
                "Opens an interactive panel with buttons to manage your evolve list. "
                "The easiest way to add, remove, view, and clear IDs!\n"
                "⏱️ Panel expires after 5 minutes."
            ),
            inline=False
        )

        embed.add_field(
            name="➕ Add IDs",
            value=(
                "**`!evolveadd <ids...>`** or **`!ea <ids...>`**\n"
                "Add Pokemon IDs to your evolve list.\n"
                "**Examples:**\n"
                "• `!ea 123 456` - Adds with 2 uses (default)\n"
                "• `!ea 789 --once` - Adds with 1 use only\n"
                "• Automatically ignores duplicate IDs\n"
                "• Add multiple IDs separated by spaces"
            ),
            inline=False
        )

        embed.add_field(
            name="➖ Remove IDs",
            value=(
                "**`!evolveremove <ids...>`** or **`!er <ids...>`**\n"
                "Remove Pokemon IDs from your list.\n"
                "**Examples:**\n"
                "• `!er 123 456` - Removes completely\n"
                "• `!er 789 --once` - Removes 1 use only\n"
                "• Remove multiple IDs at once"
            ),
            inline=False
        )

        embed.add_field(
            name="📋 View List",
            value=(
                "**`!evolvelist`** or **`!el`**\n"
                "View all Pokemon IDs in your evolve list.\n"
                "• Organized into **1x Use** and **2x Uses** tabs\n"
                "• Shows 50 IDs per page\n"
                "• Use buttons to switch tabs and navigate pages"
            ),
            inline=False
        )

        embed.add_field(
            name="⚡ Evolve IDs",
            value=(
                "**`!evolve <count>`** or **`!e <count>`**\n"
                "Evolve Pokemon IDs from your list.\n"
                "**Example:** `!e 7` evolves first 7 IDs\n"
                "• Also works as slash command: `/evolve 7`\n"
                "• Prioritizes 2x use IDs first\n"
                "• Decrements use count instead of removing\n"
                "• IDs with 2 uses become 1 use after first evolve"
            ),
            inline=False
        )

        embed.add_field(
            name="🗑️ Clear All",
            value=(
                "**`!evolveclear`** or **`!ec`**\n"
                "Remove all IDs from your evolve list.\n"
                "⚠️ This action clears your entire list!"
            ),
            inline=False
        )

        embed.add_field(
            name="🔍 How Uses Work",
            value=(
                "Each ID can have **1 or 2 uses**:\n"
                "• **2 uses:** ID evolves twice before being removed\n"
                "• **1 use:** ID evolves once then gets removed\n"
                "• Using `!evolve` prioritizes 2x IDs first\n"
                "• After one use, 2x IDs become 1x IDs"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Tip: Use the panel (!ep) for the easiest experience!")
        return embed

    def get_recording_embed(self) -> discord.Embed:
        """ID recording help embed"""
        embed = discord.Embed(
            title="📝 ID Recording",
            description="Record Pokemon IDs automatically from bot messages:",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="🎯 How to Use",
            value=(
                "**`!id`** (Reply to a message)\n\n"
                "**Steps:**\n"
                "1️⃣ Find a message with Pokemon embeds (from bot)\n"
                "2️⃣ Reply to that message with `!id`\n"
                "3️⃣ Bot starts recording IDs automatically\n"
                "4️⃣ Click **Stop Recording** button when done"
            ),
            inline=False
        )

        embed.add_field(
            name="✨ Features",
            value=(
                "• **Real-time tracking** - IDs update instantly as message edits\n"
                "• **Auto-detection** - Finds Pokemon IDs in embed descriptions\n"
                "• **Duplicate removal** - Only unique IDs are saved\n"
                "• **Auto-timeout** - Stops after 10 minutes of inactivity\n"
                "• **Manual stop** - Use the button anytime to stop\n"
                "• **Multiple recordings** - Track different messages simultaneously"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Results",
            value=(
                "When recording stops, you'll receive:\n"
                "• **Total count** of unique IDs found\n"
                "• **Sorted list** (newest to oldest)\n"
                "• **Paginated view** if more than 50 IDs\n"
                "• **Copy-ready format** in code blocks\n"
                "• **Space-separated** for easy copying"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Settings",
            value=(
                "**Timeout:** 10 minutes of no new IDs\n"
                "**IDs per page:** 50\n"
                "**Check interval:** 30 seconds\n"
                "**ID Format:** Must be in backticks (`` `123456` ``)\n\n"
                "⏱️ Timer resets when new IDs are detected!"
            ),
            inline=False
        )

        embed.add_field(
            name="💡 Pro Tips",
            value=(
                "• Works with any message containing Pokemon IDs\n"
                "• Perfect for mass spawn events\n"
                "• Can track multiple messages simultaneously\n"
                "• Anyone can stop the recording with the button\n"
                "• Results are automatically sorted by ID number\n"
                "• Detects both **`bold`** and `regular` ID formats"
            ),
            inline=False
        )

        embed.add_field(
            name="⚠️ Requirements",
            value=(
                "• Must reply to a message (use Discord's reply feature)\n"
                "• Message must contain embeds with Pokemon IDs\n"
                "• Bot needs permission to read message history\n"
                "• IDs must be in backticks: `` `123456` ``\n"
                "• Original message must not be deleted during recording"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Tip: Reply to any Pokemon bot message and use !id")
        return embed

    def get_quest_embed(self) -> discord.Embed:
        """Quest helper commands help embed"""
        embed = discord.Embed(
            title="🔍 Quest Helper Commands",
            description="Get smart Pokemon suggestions for event quests:",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="🎯 Main Command",
            value=(
                "**`!suggest [count]`** or **`!s [count]`**\n"
                "Analyzes the latest event quest embed and suggests Pokemon.\n"
                "**Examples:**\n"
                "• `!suggest` - Suggests 2 Pokemon per quest (default)\n"
                "• `!s 3` - Suggests 3 Pokemon per quest\n"
                "• Also works as slash command: `/suggest 3`"
            ),
            inline=False
        )

        embed.add_field(
            name="✨ How It Works",
            value=(
                "1️⃣ Finds the most recent event quest embed in the channel\n"
                "2️⃣ Analyzes each quest requirement (type, region, gender)\n"
                "3️⃣ Suggests Pokemon with **best spawn rates** first\n"
                "4️⃣ Shows a summary with all suggestions\n"
                "5️⃣ Click **Details** button for full quest breakdown"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Features",
            value=(
                "• **Smart prioritization** - Suggests Pokemon with spawn rates 1/225 > 1/337 > 1/674\n"
                "• **Type matching** - Finds Pokemon matching quest types (Fire, Water, etc.)\n"
                "• **Region matching** - Filters by region (Kanto, Johto, etc.)\n"
                "• **Gender quests** - Handles male, female, and genderless requirements\n"
                "• **Dual-type support** - Considers both primary and secondary types\n"
                "• **No duplicates** - Each Pokemon suggested once per event\n"
                "• **Detailed info** - Shows Dex #, types, region, and spawn rate"
            ),
            inline=False
        )

        embed.add_field(
            name="📋 Output Format",
            value=(
                "**Summary View:**\n"
                "• Complete list of all suggested Pokemon\n"
                "• Separate section for gender quest suggestions\n\n"
                "**Details View** (click button):\n"
                "• Individual quest breakdown\n"
                "• Pokemon suggestions for each quest\n"
                "• Full Pokemon information per suggestion"
            ),
            inline=False
        )

        embed.add_field(
            name="🎮 Supported Quest Types",
            value=(
                "✅ Type-based quests (Fire, Water, Grass, etc.)\n"
                "✅ Region-based quests (Kanto, Johto, etc.)\n"
                "✅ Gender-based quests (Male, Female, Genderless)\n"
                "✅ Combined quests (Type + Region)\n"
                "❌ Breeding quests (skipped automatically)"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Parameters",
            value=(
                "**Count:** 1-5 Pokemon per quest\n"
                "• Default: 2 Pokemon\n"
                "• Higher counts give more options\n"
                "• Best spawn rates prioritized first\n\n"
                "**Search Range:** Last 50 messages\n"
                "• Searches for event quest embeds\n"
                "• Must have a field with 'quest' in the name"
            ),
            inline=False
        )

        embed.add_field(
            name="💡 Pro Tips",
            value=(
                "• Run command in the same channel as event embeds\n"
                "• Use higher counts (3-5) for more variety\n"
                "• Gender quest suggestions appear separately\n"
                "• Click Details button to see quest-by-quest breakdown\n"
                "• Pokemon are sorted by spawn rate for efficiency\n"
                "• Works with any event quest format"
            ),
            inline=False
        )

        embed.add_field(
            name="⚠️ Requirements",
            value=(
                "• Event quest embed must be in recent messages (last 50)\n"
                "• Embed must have a field containing 'quest' in its name\n"
                "• Quests must follow standard format (numbered list)\n"
                "• Bot needs permission to read message history"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Tip: Use !suggest in channels with event quest embeds")
        return embed

class HelpView(discord.ui.View):
    """View for help command with dropdown and quick navigation buttons"""
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(HelpDropdown())

    def get_dropdown(self) -> HelpDropdown:
        """Get the dropdown from the view"""
        for item in self.children:
            if isinstance(item, HelpDropdown):
                return item
        return None

    @discord.ui.button(label="🏠 Home", style=discord.ButtonStyle.secondary, row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        dropdown = self.get_dropdown()
        if dropdown:
            embed = dropdown.get_home_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Release", style=discord.ButtonStyle.primary, row=1)
    async def release_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        dropdown = self.get_dropdown()
        if dropdown:
            embed = dropdown.get_release_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚡ Evolve", style=discord.ButtonStyle.primary, row=1)
    async def evolve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        dropdown = self.get_dropdown()
        if dropdown:
            embed = dropdown.get_evolve_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📝 Recording", style=discord.ButtonStyle.primary, row=1)
    async def recording_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        dropdown = self.get_dropdown()
        if dropdown:
            embed = dropdown.get_recording_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔍 Quest", style=discord.ButtonStyle.primary, row=2)
    async def quest_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        dropdown = self.get_dropdown()
        if dropdown:
            embed = dropdown.get_quest_embed()
            await interaction.response.edit_message(embed=embed, view=self)

class HelpCommands(commands.Cog):
    """Help commands for the bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', aliases=['h', 'commands', 'cmds'])
    async def help_command(self, ctx: commands.Context, category: Optional[str] = None):
        """
        Show help menu with command information.
        Usage: !help or !h
        Optional: !help <category> (release/evolve/recording/quest)
        """
        dropdown = HelpDropdown()

        if category:
            category_lower = category.lower()
            if category_lower in ['release', 'r', 'rel']:
                embed = dropdown.get_release_embed()
            elif category_lower in ['evolve', 'e', 'evo']:
                embed = dropdown.get_evolve_embed()
            elif category_lower in ['recording', 'id', 'rec', 'record']:
                embed = dropdown.get_recording_embed()
            elif category_lower in ['quest', 'q', 'suggest', 'suggestion']:
                embed = dropdown.get_quest_embed()
            else:
                embed = dropdown.get_home_embed()
        else:
            embed = dropdown.get_home_embed()

        view = HelpView()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @app_commands.command(name='help', description='Show help menu with command information')
    @app_commands.describe(category='Choose a specific category (release/evolve/recording/quest)')
    @app_commands.choices(category=[
        app_commands.Choice(name='Release Commands', value='release'),
        app_commands.Choice(name='Evolve Commands', value='evolve'),
        app_commands.Choice(name='ID Recording', value='recording'),
        app_commands.Choice(name='Quest Helper', value='quest'),
    ])
    async def help_slash(
        self, 
        interaction: discord.Interaction, 
        category: Optional[app_commands.Choice[str]] = None
    ):
        """
        Slash command version of help.
        Usage: /help
        """
        dropdown = HelpDropdown()

        if category:
            category_value = category.value if hasattr(category, 'value') else category
            if category_value == 'release':
                embed = dropdown.get_release_embed()
            elif category_value == 'evolve':
                embed = dropdown.get_evolve_embed()
            elif category_value == 'recording':
                embed = dropdown.get_recording_embed()
            elif category_value == 'quest':
                embed = dropdown.get_quest_embed()
            else:
                embed = dropdown.get_home_embed()
        else:
            embed = dropdown.get_home_embed()

        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
