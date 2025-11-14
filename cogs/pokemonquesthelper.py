import discord
from discord.ext import commands
from discord import app_commands
import csv
import re
from typing import List, Dict, Optional
from config import EMBED_COLOR

class DetailsView(discord.ui.View):
    """View with a Details button to show full quest breakdown"""

    def __init__(self, details_embed, timeout=180):
        super().__init__(timeout=timeout)
        self.details_embed = details_embed

    @discord.ui.button(label='View Details', style=discord.ButtonStyle.primary, emoji='📋')
    async def details_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=self.details_embed, ephemeral=True)

class PokemonQuestHelper(commands.Cog):
    """Cog for suggesting Pokémon based on event quests"""

    def __init__(self, bot):
        self.bot = bot
        self.pokemon_data = {}
        self.spawn_rates = {}
        self.gender_data = {'male': set(), 'female': set(), 'genderless': set()}
        self.AUTO_SUGGEST_CHANNEL_ID = 1429692867022164018  # Channel to monitor
        self.processed_messages = set()  # Track processed message IDs
        self.load_data()

    def is_regional_variant(self, pokemon_name: str) -> bool:
        """Check if a Pokémon is a regional variant"""
        regional_prefixes = ['alolan', 'galarian', 'hisuian', 'paldean']
        name_lower = pokemon_name.lower()
        return any(prefix in name_lower for prefix in regional_prefixes)

    def load_data(self):
        """Load Pokémon data and spawn rates from CSV files"""
        try:
            # Load pokemondata.csv (tab-separated)
            with open('pokemondata.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    dex = int(row['Dex'])
                    self.pokemon_data[dex] = {
                        'name': row['Name'],
                        'type1': row['Type 1'],
                        'type2': row['Type 2'].strip() if row['Type 2'].strip() else None,
                        'dex': dex,
                        'region': self.get_region(dex)
                    }

            # Load spawnrates.csv (comma-separated)
            with open('spawnrates.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dex = int(row['Dex'])
                    self.spawn_rates[dex] = row['Chance']

            # Load gender data
            for gender_type in ['male', 'female', 'genderless']:
                try:
                    with open(f'{gender_type}.csv', 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row:
                                self.gender_data[gender_type].add(row['name'].strip())
                except FileNotFoundError:
                    print(f'Warning: {gender_type}.csv not found')

            print(f'✓ Loaded {len(self.pokemon_data)} Pokémon and {len(self.spawn_rates)} spawn rates')
            print(f'✓ Loaded gender data: {len(self.gender_data["male"])} male, {len(self.gender_data["female"])} female, {len(self.gender_data["genderless"])} genderless')
        except Exception as e:
            print(f'✗ Error loading Pokémon data: {e}')

    def get_region(self, dex: int) -> str:
        """Get region based on Dex number"""
        if 1 <= dex <= 151:
            return 'Kanto'
        elif 152 <= dex <= 251:
            return 'Johto'
        elif 252 <= dex <= 386:
            return 'Hoenn'
        elif 387 <= dex <= 493:
            return 'Sinnoh'
        elif 494 <= dex <= 649:
            return 'Unova'
        elif 650 <= dex <= 721:
            return 'Kalos'
        elif 722 <= dex <= 809:
            return 'Alola'
        elif 810 <= dex <= 905:
            return 'Galar'
        elif 906 <= dex <= 1025:
            return 'Paldea'
        return 'Unknown'

    def parse_quest(self, quest_text: str) -> Optional[Dict]:
        """Parse a quest line to extract requirements and determine quest type"""
        quest_text_lower = quest_text.lower()

        # Identify quest type
        quest_type = None

        # Check for breeding quests
        if 'breed' in quest_text_lower:
            quest_type = 'breed'

        # Check for release quests
        elif 'release' in quest_text_lower:
            quest_type = 'release'

        # Check for gender quests
        elif 'female' in quest_text_lower:
            quest_type = 'gender'
            gender = 'female'
        elif 'male' in quest_text_lower:
            quest_type = 'gender'
            gender = 'male'
        elif 'unknown gender' in quest_text_lower or 'genderless' in quest_text_lower:
            quest_type = 'gender'
            gender = 'genderless'

        # Check for region quests
        regions = ['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar', 'Paldea']
        has_region = None
        for region in regions:
            if region in quest_text:
                has_region = region
                break

        # Check for type quests
        types = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 
                'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 
                'Steel', 'Fairy']
        has_type = None
        for ptype in types:
            if ptype.lower() in quest_text_lower or f'{ptype}-type' in quest_text:
                has_type = ptype
                break

        # Determine quest type if not already set
        if not quest_type:
            if has_region or has_type:
                quest_type = 'type_region'
            elif 'catch' in quest_text_lower:
                quest_type = 'generic_catch'
            else:
                quest_type = 'unknown'

        # Extract count
        count = 0
        count_match = re.search(r'(?:Catch|Release|Breed)\s+(\d+)', quest_text, re.IGNORECASE)
        if count_match:
            count = int(count_match.group(1))

        # Build quest info
        quest_info = {
            'text': quest_text,
            'type': quest_type,
            'region': has_region,
            'pokemon_type': has_type,
            'count': count,
            'gender': gender if quest_type == 'gender' else None
        }

        return quest_info

    def find_matching_pokemon(self, quest_info: Dict, limit: int = 2) -> List[Dict]:
        """Find Pokémon matching the quest criteria"""
        matches = []
        quest_type = quest_info['type']

        # Skip quests that don't need suggestions
        if quest_type in ['breed', 'release', 'generic_catch', 'unknown']:
            return matches

        # Handle gender quests
        if quest_type == 'gender':
            gender = quest_info['gender']
            gender_pokemon = self.gender_data.get(gender, set())

            spawn_priorities = ['1/225', '1/337', '1/674']

            for priority in spawn_priorities:
                if len(matches) >= limit:
                    break

                for dex, data in self.pokemon_data.items():
                    if len(matches) >= limit:
                        break

                    if any(m['dex'] == dex for m in matches):
                        continue

                    if self.is_regional_variant(data['name']):
                        continue

                    if data['name'] in gender_pokemon and dex in self.spawn_rates and self.spawn_rates[dex] == priority:
                        matches.append({**data, 'spawn_rate': self.spawn_rates[dex]})

            return matches[:limit]

        # Handle type/region quests
        if quest_type == 'type_region':
            spawn_priorities = ['1/225', '1/337', '1/674']

            for priority in spawn_priorities:
                if len(matches) >= limit:
                    break

                for dex, data in self.pokemon_data.items():
                    if len(matches) >= limit:
                        break

                    if any(m['dex'] == dex for m in matches):
                        continue

                    if self.is_regional_variant(data['name']):
                        continue

                    if dex not in self.spawn_rates or self.spawn_rates[dex] != priority:
                        continue

                    # Check matching criteria
                    region_match = not quest_info['region'] or data['region'] == quest_info['region']
                    type_match = not quest_info['pokemon_type'] or (
                        data['type1'] == quest_info['pokemon_type'] or 
                        data['type2'] == quest_info['pokemon_type']
                    )

                    # Priority: both match > type match > region match
                    if quest_info['region'] and quest_info['pokemon_type']:
                        if region_match and type_match:
                            matches.append({**data, 'spawn_rate': self.spawn_rates[dex]})
                    elif quest_info['pokemon_type']:
                        if type_match:
                            matches.append({**data, 'spawn_rate': self.spawn_rates[dex]})
                    elif quest_info['region']:
                        if region_match:
                            matches.append({**data, 'spawn_rate': self.spawn_rates[dex]})

        return matches[:limit]

    def format_pokemon_info(self, pokemon: Dict) -> str:
        """Format Pokémon information for display"""
        types = pokemon['type1']
        if pokemon['type2']:
            types += f"/{pokemon['type2']}"

        return f"• **{pokemon['name']}** (#{pokemon['dex']:03d}, {types}, {pokemon['region']}, {pokemon['spawn_rate']})"

    def is_quest_embed(self, embed: discord.Embed) -> bool:
        """Check if an embed contains quest information"""
        if not embed.fields:
            return False

        for field in embed.fields:
            field_name_lower = field.name.lower()
            if any(keyword in field_name_lower for keyword in ['quest', 'task', 'security', 'challenge']):
                if re.search(r'\d+\..*[Cc]atch', field.value):
                    return True
        return False

    async def process_quest_embed(self, message: discord.Message, count: int = 2, include_gender: bool = True, reply_to_message: bool = True):
        """Process a quest embed and send suggestions"""
        embed = message.embeds[0]

        # Find the quest field
        quest_field = None
        for field in embed.fields:
            field_name_lower = field.name.lower()
            if any(keyword in field_name_lower for keyword in ['quest', 'task', 'security', 'challenge']):
                quest_field = field
                break

        if not quest_field:
            return None

        # Parse quests from the field value
        quest_lines = quest_field.value.split('\n')

        # Build summary embed
        summary_embed = discord.Embed(
            title='📋 Pokémon Quest Suggestions',
            description=f'These Pokémon will help you complete the maximum number of quests efficiently.\nShowing **{count} Pokémon** per quest from: **{embed.title}**',
            color=EMBED_COLOR
        )

        # Build detailed embed
        details_embed = discord.Embed(
            title='📋 Quest Details',
            description=f'Complete breakdown for: **{embed.title}**',
            color=EMBED_COLOR
        )

        suggestions = []
        all_suggested_pokemon = set()
        gender_suggestions = []

        for line in quest_lines:
            if not line.strip() or not re.search(r'^\d+\.', line.strip()):
                continue

            quest_info = self.parse_quest(line)
            if not quest_info:
                continue

            # Skip gender quests if not included
            if quest_info['type'] == 'gender' and not include_gender:
                continue

            matches = self.find_matching_pokemon(quest_info, limit=count)

            if matches:
                quest_text = re.sub(r'<:[^>]+>', '', quest_info['text'])
                quest_text = re.sub(r'`\d+/\d+`', '', quest_text).strip()

                suggestion_text = f"**Quest:** {quest_text}\n"
                for pokemon in matches:
                    suggestion_text += self.format_pokemon_info(pokemon) + '\n'

                # Separate gender quests from regular quests
                if quest_info['type'] == 'gender':
                    gender_pokemon_names = ', '.join([p['name'] for p in matches])
                    gender_suggestions.append({
                        'text': f"**{quest_text}**\n• {gender_pokemon_names}",
                        'quest_text': quest_text,
                        'pokemon': gender_pokemon_names
                    })
                else:
                    for pokemon in matches:
                        all_suggested_pokemon.add(pokemon['name'])

                suggestions.append(suggestion_text)

        if suggestions:
            # Add quest details to the details embed
            for suggestion in suggestions[:25]:
                details_embed.add_field(
                    name='',
                    value=suggestion,
                    inline=False
                )

            # Add main Pokémon list to summary embed (excluding gender quests)
            if all_suggested_pokemon:
                pokemon_list = ', '.join(sorted(all_suggested_pokemon))
                summary_embed.add_field(
                    name='📝 Suggested Pokémon',
                    value=pokemon_list,
                    inline=False
                )

                details_embed.add_field(
                    name='📝 Complete List',
                    value=pokemon_list,
                    inline=False
                )

            # Add gender quest suggestions separately
            if gender_suggestions:
                # Add separator before gender quests
                summary_embed.add_field(
                    name='─────────────────────',
                    value='',
                    inline=False
                )
                
                for gender_info in gender_suggestions:
                    # Get gender type, default to "Gender" if not present (shouldn't happen but safety check)
                    gender_type = gender_info.get('gender_type', 'Gender')
                    field_name = f'{gender_type} Pokémon'
                    summary_embed.add_field(
                        name=field_name,
                        value=gender_info['text'],
                        inline=False
                    )

            if len(suggestions) > 25:
                details_embed.set_footer(text=f'Showing 25 of {len(suggestions)} quests')

            summary_embed.set_footer(text='Click "View Details" for the complete breakdown')

            # Create view with Details button
            view = DetailsView(details_embed)

            if reply_to_message:
                return await message.reply(embed=summary_embed, view=view, mention_author=False)
            else:
                return (summary_embed, view)
        
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for quest embeds in the monitored channel"""
        if message.channel.id != self.AUTO_SUGGEST_CHANNEL_ID:
            return

        if message.id in self.processed_messages:
            return

        if message.embeds and self.is_quest_embed(message.embeds[0]):
            self.processed_messages.add(message.id)

            if len(self.processed_messages) > 100:
                self.processed_messages = set(list(self.processed_messages)[-100:])

            await self.process_quest_embed(message, count=2, include_gender=True)

    @commands.command(name='suggest', aliases=['s'])
    async def suggest_prefix(self, ctx, count: int = 2, gender: bool = False):
        """Get Pokémon suggestions for quest"""
        if count < 1 or count > 5:
            await ctx.reply('❌ Please choose between 1 and 5 Pokémon per quest!', mention_author=False)
            return

        # Check if user replied to a message
        if hasattr(ctx.message, 'reference') and ctx.message.reference:
            try:
                replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

                if replied_message.embeds and self.is_quest_embed(replied_message.embeds[0]):
                    await self.process_quest_embed(replied_message, count, include_gender=gender)
                    return
                else:
                    await ctx.reply('❌ That message doesn\'t contain a quest embed!', mention_author=False)
                    return
            except discord.NotFound:
                await ctx.reply('❌ Message not found!', mention_author=False)
                return
            except discord.HTTPException:
                await ctx.reply('❌ An error occurred while fetching the message!', mention_author=False)
                return

        # Find the latest message with a quest embed
        async for message in ctx.channel.history(limit=50):
            if message.embeds and self.is_quest_embed(message.embeds[0]):
                await self.process_quest_embed(message, count, include_gender=gender)
                return

        await ctx.reply('❌ No quest embeds found in recent messages!', mention_author=False)

    @app_commands.command(name='suggest', description='Get Pokémon suggestions for quest')
    @app_commands.describe(
        count='Number of Pokémon to suggest per quest (default: 2)',
        gender='Include gender-specific suggestions (default: no)'
    )
    async def suggest_slash(self, interaction: discord.Interaction, count: int = 2, gender: bool = False):
        """Get Pokémon suggestions for quest"""
        if count < 1 or count > 5:
            await interaction.response.send_message('❌ Please choose between 1 and 5 Pokémon per quest!', ephemeral=True)
            return

        await interaction.response.defer()

        # Find the latest message with a quest embed
        async for message in interaction.channel.history(limit=50):
            if message.embeds and self.is_quest_embed(message.embeds[0]):
                await self.process_quest_embed(message, count, include_gender=gender)
                await interaction.followup.send('✅ Quest suggestions generated!', ephemeral=True)
                return

        await interaction.followup.send('❌ No quest embeds found in recent messages!', ephemeral=True)

async def setup(bot):
    cog = PokemonQuestHelper(bot)
    
    # Define context menu outside the class
    @app_commands.context_menu(name='Quest Suggestions')
    async def suggest_context(interaction: discord.Interaction, message: discord.Message):
        """Right-click context menu command to get quest suggestions"""
        # Check if the message has embeds and is a quest embed
        if not message.embeds:
            await interaction.response.send_message('❌ That message doesn\'t contain any embeds!', ephemeral=True)
            return

        if not cog.is_quest_embed(message.embeds[0]):
            await interaction.response.send_message('❌ That message doesn\'t contain a quest embed!', ephemeral=True)
            return

        await interaction.response.defer()

        # Process the quest embed with default settings (count=2, gender=True)
        result = await cog.process_quest_embed(message, count=2, include_gender=True, reply_to_message=False)

        if result:
            summary_embed, view = result
            await interaction.followup.send(embed=summary_embed, view=view)
        else:
            await interaction.followup.send('❌ No quest suggestions could be generated!', ephemeral=True)
    
    # Add context menu to bot
    bot.tree.add_command(suggest_context)
    
    # Add cog
    await bot.add_cog(cog)
