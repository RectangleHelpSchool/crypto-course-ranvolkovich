import asyncio
import logging
from datetime import datetime, timezone

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from web3.types import LogReceipt

from src.approvalfetcher.clients.web3_client import Web3Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BADGER_WBTC_TOKEN = "0x4b92d19c11435614CD49Af1b589001b7c08cD4D5"
APPROVAL_EVENT_SIGNATURE = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

START_DATE = datetime(2021, 9, 1, tzinfo=timezone.utc)
END_DATE = datetime(2022, 1, 31, tzinfo=timezone.utc)


async def get_block_by_timestamp(client: Web3Client, target_timestamp: int, start_block: int = 1, end_block: int | None = None) -> int:
    if end_block is None:
        end_block = await client.get_latest_block()

    while start_block <= end_block:
        mid_block = (start_block + end_block) // 2
        block = await client.w3.eth.get_block(mid_block)
        block_timestamp = block['timestamp']

        if block_timestamp < target_timestamp:
            start_block = mid_block + 1
        elif block_timestamp > target_timestamp:
            end_block = mid_block - 1
        else:
            return mid_block

    return start_block


async def fetch_token_approvals(client: Web3Client, token_address: str, from_block: int, to_block: int) -> list[LogReceipt]:
    logger.info(f"Fetching approval events for token {token_address} from block {from_block} to {to_block}")

    logs = await client.w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': to_block,
        'address': token_address,
        'topics': [APPROVAL_EVENT_SIGNATURE]
    })

    logger.info(f"Found {len(logs)} approval events")
    return logs


async def parse_approval_log(client: Web3Client, log: LogReceipt, block_cache: dict) -> dict:
    topics = log['topics']

    owner_topic = topics[1].hex()
    owner = "0x" + owner_topic[-40:]

    spender_topic = topics[2].hex()
    spender = "0x" + spender_topic[-40:]

    block_number = log['blockNumber']

    if block_number not in block_cache:
        await asyncio.sleep(0.1)
        block = await client.w3.eth.get_block(block_number)
        block_cache[block_number] = block['timestamp']

    timestamp = datetime.fromtimestamp(block_cache[block_number], tz=timezone.utc)

    return {
        'owner': owner.lower(),
        'spender': spender.lower(),
        'block_number': block_number,
        'timestamp': timestamp,
        'tx_hash': log['transactionHash'].hex()
    }


async def collect_approvals_data(client: Web3Client, token_address: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    logger.info(f"Finding block range for {start_date} to {end_date}")
    from_block = await get_block_by_timestamp(client, start_timestamp)
    to_block = await get_block_by_timestamp(client, end_timestamp)

    logger.info(f"Block range: {from_block} to {to_block}")

    logs = await fetch_token_approvals(client, token_address, from_block, to_block)

    logger.info("Parsing approval events...")
    block_cache = {}
    tasks = [parse_approval_log(client, log, block_cache) for log in logs]
    approvals = await asyncio.gather(*tasks)

    df = pd.DataFrame(approvals)
    logger.info(f"Collected {len(df)} approvals")

    return df


def analyze_time_windows(df: pd.DataFrame, window_size: str = 'W') -> pd.DataFrame:
    df['date'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('date')

    window_stats = []

    grouped = df.groupby(pd.Grouper(freq=window_size))

    for window_date, window_data in grouped:
        if len(window_data) == 0:
            continue

        spender_counts = window_data['spender'].value_counts()

        window_stats.append({
            'window_start': window_date,
            'total_approvals': len(window_data),
            'unique_owners': window_data['owner'].nunique(),
            'unique_spenders': window_data['spender'].nunique(),
            'top_spender': spender_counts.index[0] if len(spender_counts) > 0 else None,
            'top_spender_count': spender_counts.iloc[0] if len(spender_counts) > 0 else 0,
            'top_spender_percentage': (spender_counts.iloc[0] / len(window_data) * 100) if len(spender_counts) > 0 else 0
        })

    stats_df = pd.DataFrame(window_stats)

    stats_df['approval_change_pct'] = stats_df['total_approvals'].pct_change() * 100
    stats_df['top_spender_change_pct'] = stats_df['top_spender_count'].pct_change() * 100

    return stats_df


def detect_anomalies(stats_df: pd.DataFrame, threshold_pct: float = 100.0) -> pd.DataFrame:
    anomalies = stats_df[stats_df['approval_change_pct'] > threshold_pct].copy()

    logger.info(f"\nDetected {len(anomalies)} anomalous windows with >{threshold_pct}% increase:")
    for _, row in anomalies.iterrows():
        logger.info(f"  {row['window_start'].date()}: {row['approval_change_pct']:.1f}% increase "
                   f"({row['total_approvals']} approvals, top spender: {row['top_spender'][:10]}...)")

    return anomalies


def visualize_analysis(df: pd.DataFrame, stats_df: pd.DataFrame, anomalies: pd.DataFrame):
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    axes[0].plot(stats_df['window_start'], stats_df['total_approvals'], marker='o', linewidth=1, markersize=3)
    if not anomalies.empty:
        axes[0].scatter(anomalies['window_start'], anomalies['total_approvals'],
                       color='red', s=100, zorder=5, label='Anomalies', marker='X')
    axes[0].set_title('Total Approvals per Hour', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Date')
    axes[0].set_ylabel('Number of Approvals')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    axes[1].bar(stats_df['window_start'], stats_df['approval_change_pct'],
               color=['red' if x > 200 else 'orange' if x > 100 else 'blue' for x in stats_df['approval_change_pct']],
               width=0.04)
    axes[1].axhline(y=200, color='red', linestyle='--', label='200% threshold', linewidth=2)
    axes[1].set_title('Hour-over-Hour Approval Change (%)', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Date')
    axes[1].set_ylabel('Change (%)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    top_spenders = df['spender'].value_counts().head(10)
    spender_timeline = []
    for spender in top_spenders.index:
        spender_data = df[df['spender'] == spender]
        spender_by_day = spender_data.set_index(pd.to_datetime(spender_data['timestamp'])).groupby(pd.Grouper(freq='D')).size()
        spender_timeline.append(spender_by_day)

    spender_df = pd.DataFrame(spender_timeline).T
    spender_df.columns = [f"{s[:6]}...{s[-4:]}" for s in top_spenders.index]
    spender_df = spender_df.fillna(0)

    spender_df.plot(ax=axes[2], kind='bar', stacked=True, width=0.8)
    axes[2].set_title('Top 10 Spenders - Approvals Over Time (Daily)', fontsize=14, fontweight='bold')
    axes[2].set_xlabel('Date')
    axes[2].set_ylabel('Number of Approvals')
    axes[2].legend(title='Spenders', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    axes[2].grid(True, alpha=0.3, axis='y')
    axes[2].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig('badger_dao_analysis.png', dpi=300, bbox_inches='tight')
    logger.info("\nVisualization saved to 'badger_dao_analysis.png'")
    plt.show()


async def main():
    logger.info("Starting BadgerDAO Attack Analysis")
    logger.info(f"Token: {BADGER_WBTC_TOKEN}")
    logger.info(f"Date Range: {START_DATE.date()} to {END_DATE.date()}")

    async with Web3Client() as client:
        df = await collect_approvals_data(client, BADGER_WBTC_TOKEN, START_DATE, END_DATE)

        if df.empty:
            logger.error("No approval events found in the specified date range")
            return

        logger.info("\n" + "="*60)
        logger.info("ANALYZING TIME WINDOWS - HOURLY")
        logger.info("="*60)

        stats_df_hourly = analyze_time_windows(df, window_size='h')

        logger.info("\n" + "="*60)
        logger.info("ANALYZING TIME WINDOWS - DAILY")
        logger.info("="*60)

        stats_df_daily = analyze_time_windows(df, window_size='D')

        print("\nDaily Statistics (showing days with activity):")
        print(stats_df_daily[stats_df_daily['total_approvals'] > 0].to_string())

        logger.info("\n" + "="*60)
        logger.info("DETECTING ANOMALIES (Hourly Analysis)")
        logger.info("="*60)

        anomalies_hourly = detect_anomalies(stats_df_hourly, threshold_pct=200.0)

        logger.info("\n" + "="*60)
        logger.info("DETECTING ANOMALIES (Daily Analysis)")
        logger.info("="*60)

        anomalies_daily = detect_anomalies(stats_df_daily, threshold_pct=100.0)

        stats_df = stats_df_hourly
        anomalies = anomalies_hourly

        if not anomalies.empty:
            logger.info("\nTop Spenders in Anomalous Hours:")
            for _, anomaly in anomalies.iterrows():
                hour_data = df[(pd.to_datetime(df['timestamp']) >= anomaly['window_start']) &
                              (pd.to_datetime(df['timestamp']) < anomaly['window_start'] + pd.Timedelta(hours=1))]
                top_spenders = hour_data['spender'].value_counts().head(5)
                logger.info(f"\n  Hour: {anomaly['window_start']}:")
                for spender, count in top_spenders.items():
                    logger.info(f"    {spender}: {count} approvals ({count/len(hour_data)*100:.1f}%)")

        logger.info("\n" + "="*60)
        logger.info("GENERATING VISUALIZATIONS")
        logger.info("="*60)

        visualize_analysis(df, stats_df, anomalies)

        logger.info("\nAnalysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
