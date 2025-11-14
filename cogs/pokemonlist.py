import discord
from discord.ext import commands
from discord import app_commands
import csv
from typing import List, Dict, Optional
from config import EMBED_COLOR

class PokemonListHelper(commands.Cog):
    """Cog for listing Pokémon based on type and region filters"""

    def __init__(self, bot):
        self.bot = bot
        self.pokemon_data = {}
        self.spawn_rates = {}
        self.load_data()

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

            print(f'Loaded {len(self.pokemon_data)} Pokémon and {len(self.spawn_rates)} spawn rates')
        except Exception as e:
            print(f'Error loading Pokémon data: {e}')

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

    def parse_list_command(self, args: str) -> Optional[Dict]:
        """Parse command arguments to extract filters"""
        filters = {
            'types': [],
            'region': None,
            'show_all': False
        }

        # Split by -- to get individual flags
        parts = args.split('--')

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check for type filter
            if part.startswith('t '):
                type_name = part[2:].strip().capitalize()
                if len(filters['types']) < 2:  # Max 2 type filters
                    filters['types'].append(type_name)

            # Check for region filter
            elif part.startswith('r '):
                region_name = part[2:].strip().capitalize()
                filters['region'] = region_name

            # Check for --all flag
            elif part == 'all':
                filters['show_all'] = True

        return filters

    def find_matching_pokemon(self, filters: Dict) -> Dict[str, List[str]]:
        """Find Pokémon matching the filters, grouped by spawn rate"""
        spawn_rate_groups = {
            '1/225': [],
            '1/337': [],
            '1/674': [],
            '1/899': []
        }

        for dex, data in self.pokemon_data.items():
            # Check if Pokémon has spawn rate data
            if dex not in self.spawn_rates:
                continue

            spawn_rate = self.spawn_rates[dex]

            # Skip if spawn rate is not in our groups (unless --all is used)
            if not filters['show_all'] and spawn_rate not in spawn_rate_groups:
                continue

            # Check region filter
            if filters['region'] and data['region'] != filters['region']:
                continue

            # Check type filters
            if len(filters['types']) == 2:
                # Both types must match (order doesn't matter)
                type1, type2 = filters['types']
                has_both_types = (
                    (data['type1'] == type1 and data['type2'] == type2) or
                    (data['type1'] == type2 and data['type2'] == type1)
                )
                if not has_both_types:
                    continue
            elif len(filters['types']) == 1:
                # At least one type must match
                type_name = filters['types'][0]
                if data['type1'] != type_name and data['type2'] != type_name:
                    continue

            # Add to appropriate spawn rate group
            if spawn_rate in spawn_rate_groups:
                spawn_rate_groups[spawn_rate].append(data['name'])
            elif filters['show_all']:
                # If --all is used, add to 1/899 group for rates beyond it
                spawn_rate_groups['1/899'].append(data['name'])

        # Sort each group alphabetically
        for rate in spawn_rate_groups:
            spawn_rate_groups[rate].sort()

        return spawn_rate_groups

    def format_list_embed(self, spawn_rate_groups: Dict[str, List[str]], filters: Dict) -> discord.Embed:
        """Format the Pokémon list into an embed"""
        # Build title based on filters
        title_parts = []
        if filters['types']:
            if len(filters['types']) == 2:
                title_parts.append(f"{filters['types'][0]}/{filters['types'][1]}")
            else:
                title_parts.append(filters['types'][0])
        if filters['region']:
            title_parts.append(filters['region'])

        title = f"📋 Pokémon List Organized By Spawnrates: {' '.join(title_parts)}" if title_parts else "📋 Pokémon List Organized By Spawnrates"

        embed = discord.Embed(
            title=title,
            color=EMBED_COLOR
        )

        # Add each spawn rate group
        spawn_order = ['1/225', '1/337', '1/674', '1/899']

        for rate in spawn_order:
            pokemon_list = spawn_rate_groups[rate]
            if pokemon_list:
                value = ', '.join(pokemon_list)
                # Truncate if too long (Discord limit is 1024 per field)
                if len(value) > 1024:
                    value = value[:1020] + '...'
                embed.add_field(
                    name=f'**{rate}**',
                    value=value,
                    inline=False
                )
            else:
                embed.add_field(
                    name=f'**{rate}**',
                    value='—',
                    inline=False
                )

        # If --all flag is used, add combined list at the end
        if filters['show_all']:
            all_pokemon = []
            for rate in spawn_order:
                all_pokemon.extend(spawn_rate_groups[rate])

            if all_pokemon:
                combined_list = ', '.join(sorted(set(all_pokemon)))
                # Truncate if too long
                if len(combined_list) > 1024:
                    combined_list = combined_list[:1020] + '...'
                embed.add_field(
                    name='**All Pokémon**',
                    value=combined_list,
                    inline=False
                )

        # Add filter info to footer
        filter_info = []
        if filters['types']:
            filter_info.append(f"Types: {', '.join(filters['types'])}")
        if filters['region']:
            filter_info.append(f"Region: {filters['region']}")
        if filters['show_all']:
            filter_info.append("All spawn rates")
        else:
            filter_info.append("Up to 1/899")

        total_count = sum(len(group) for group in spawn_rate_groups.values())
        filter_info.append(f"Total: {total_count}")

        embed.set_footer(text=' | '.join(filter_info))

        return embed

    @commands.hybrid_command(name='list', aliases=['l'], description='List Pokémon by type and region filters')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def list_pokemon(self, ctx, *, args: str = ''):
        """
        List Pokémon based on filters
        Usage: !list --t type1 --t type2 --r region --all
        Example: !list --t dragon --t ice --r paldea
        """
        if not args:
            await ctx.reply('❌ Please provide filters. Usage: `!list --t type --r region --all`\nExample: `!list --t dragon --t ice --r paldea`', mention_author=False)
            return

        # Parse filters
        filters = self.parse_list_command(args)

        # Validate filters
        if not filters['types'] and not filters['region']:
            await ctx.reply('❌ Please provide at least one type or region filter.', mention_author=False)
            return

        # Defer if this might take time
        if isinstance(ctx, discord.Interaction):
            await ctx.response.defer()

        # Find matching Pokémon
        spawn_rate_groups = self.find_matching_pokemon(filters)

        # Check if any Pokémon were found
        total_found = sum(len(group) for group in spawn_rate_groups.values())
        if total_found == 0:
            await ctx.reply('❌ No Pokémon found matching the specified filters.', mention_author=False)
            return

        # Format and send embed
        embed = self.format_list_embed(spawn_rate_groups, filters)

        try:
            if isinstance(ctx, discord.Interaction):
                await ctx.followup.send(embed=embed)
            else:
                await ctx.reply(embed=embed, mention_author=False)
        except discord.HTTPException as e:
            await ctx.reply(f'❌ Failed to send response. The list might be too large. Error: {e}', mention_author=False)

async def setup(bot):
    await bot.add_cog(PokemonListHelper(bot))
