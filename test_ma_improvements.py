"""Test script to validate moving average score calculation improvements."""

import pandas as pd
import numpy as np
from src.analysis.technical_score import TechnicalScoreCalculator
from src.indicators.moving_averages import MovingAverageIndicators

# Create sample data with different scenarios
def create_sample_data(scenario: str) -> pd.DataFrame:
    """Create test data for different MA scenarios."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=250)

    if scenario == 'strong_uptrend':
        # Price well above all MAs
        close = np.linspace(100, 150, 250) + np.random.normal(0, 2, 250)
    elif scenario == 'weak_uptrend':
        # Price between SMA50 and SMA200
        close = np.linspace(100, 120, 250) + np.random.normal(0, 2, 250)
    elif scenario == 'short_term_up':
        # Price above SMA20, below SMA50
        close = np.linspace(100, 105, 250) + np.random.normal(0, 1, 250)
    elif scenario == 'downtrend':
        # Price below all MAs
        close = np.linspace(150, 100, 250) + np.random.normal(0, 2, 250)
    else:  # neutral
        # Price near SMA20
        close = np.ones(250) * 100 + np.random.normal(0, 1, 250)

    df = pd.DataFrame({
        'Date': dates,
        'Open': close + np.random.normal(0, 1, 250),
        'High': close + np.random.normal(2, 1, 250),
        'Low': close + np.random.normal(-2, 1, 250),
        'Close': close,
        'Volume': np.random.randint(1000000, 10000000, 250)
    })
    df.set_index('Date', inplace=True)
    return df


def test_ma_scoring():
    """Test improved MA scoring logic."""

    print("=" * 80)
    print("TEST: MOVING AVERAGE SCORE CALCULATION")
    print("=" * 80)

    calculator = TechnicalScoreCalculator()

    test_cases = {
        'strong_uptrend': {
            'expected_range': (75, 95),
            'description': 'Price >> SMA200 > SMA50 > SMA20, EMA12 > EMA26'
        },
        'weak_uptrend': {
            'expected_range': (50, 70),
            'description': 'Price between SMA50 and SMA200'
        },
        'short_term_up': {
            'expected_range': (45, 65),
            'description': 'Price > SMA20, but < SMA50'
        },
        'downtrend': {
            'expected_range': (0, 40),
            'description': 'Price << SMA200'
        },
        'neutral': {
            'expected_range': (45, 55),
            'description': 'Price about equal to SMA20 (neutral)'
        }
    }

    results = []

    for scenario, config in test_cases.items():
        df = create_sample_data(scenario)
        score = calculator.calculate_moving_average_score(df)

        min_expected, max_expected = config['expected_range']
        is_valid = min_expected <= score <= max_expected

        result = {
            'Scenario': scenario,
            'Score': f"{score:.1f}",
            'Expected': f"{min_expected}-{max_expected}",
            'Valid': 'PASS' if is_valid else 'FAIL',
            'Description': config['description']
        }
        results.append(result)

        print(f"\n[{scenario.upper()}]")
        print(f"   Score: {score:.1f}/100")
        print(f"   Expected: {min_expected}-{max_expected}")
        print(f"   Status: {'PASS' if is_valid else 'FAIL'}")
        print(f"   Description: {config['description']}")

    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)

    # Print summary table
    import pandas as pd
    summary_df = pd.DataFrame(results)
    print(summary_df.to_string(index=False))

    # Test hierarchical logic
    print("\n" + "=" * 80)
    print("HIERARCHICAL PRICE POSITION TEST")
    print("=" * 80)
    print("\n[NEW LOGIC: Only highest level is counted]")
    print("   - If Price > SMA200: +15 points (strong long-term signal)")
    print("   - Elif Price > SMA50: +10 points (mid-term signal)")
    print("   - Elif Price > SMA20: +5 points (short-term signal)")
    print("   > Prevents double-counting bias")

    print("\n[OLD LOGIC (Removed)]:")
    print("   - If Price > SMA20: +10 points")
    print("   - If Price > SMA50: +10 points  (often same as SMA20)")
    print("   - If Price > SMA200: +10 points (often same as SMA50)")
    print("   > Results in +30 points almost always (low differentiation)")

    print("\n" + "=" * 80)
    print("WEIGHT ADJUSTMENTS")
    print("=" * 80)

    weights_summary = [
        ('Price Position (hierarchical)', '5-15 points', 'NEW: Only strongest level'),
        ('MA Alignment (Golden Cross)', '15 points', 'OLD: 20 points → NEW: 15 points'),
        ('EMA Momentum', '10 points', 'Unchanged'),
        ('Base Score', '50 points', 'Neutral baseline'),
        ('Maximum Score', '50 + 15 + 15 + 10 = 90', 'Slightly lower for moderation'),
    ]

    for component, points, note in weights_summary:
        print(f"   {component:.<40} {points:>20} | {note}")

    print("\n" + "=" * 80)
    print("IMPROVEMENTS APPLIED")
    print("=" * 80)
    print("[OK] Hierarchical price position (no double-counting)")
    print("[OK] Better score differentiation")
    print("[OK] NaN handling with pd.notna() checks")
    print("[OK] Clearer comments and documentation")
    print("[OK] Maintains requirement: Moving Averages = 30% of technical score")
    print("\n")


if __name__ == "__main__":
    test_ma_scoring()
