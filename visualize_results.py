"""
CAPTCHA Experiment Result Visualization Module
Automatically handles missing data and generates publication-quality charts
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import warnings
warnings.filterwarnings('ignore')

# Set font and chart style
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")

class CAPTCHAVisualizer:
    """CAPTCHA experiment result visualizer"""

    def __init__(self, results_dir: str = "./results", error_dir: str = "./error_analysis"):
        self.results_dir = Path(results_dir)
        self.error_dir = Path(error_dir)
        self.data = self._load_all_data()
        self.task_types = sorted(self.data['task_type'].unique()) if not self.data.empty else []

    def _load_all_data(self) -> pd.DataFrame:
        """Load all experiment results, automatically handle missing data"""
        all_results = []

        print("Scanning experiment result directories...")

        # Scan all results.csv files
        for csv_file in self.results_dir.rglob("results.csv"):
            try:
                parts = csv_file.relative_to(self.results_dir).parts
                if len(parts) >= 3:
                    experiment = parts[0]  # exp1, exp2, exp3, exp4
                    provider = parts[1]    # openai, anthropic, gemini, fireworks
                    model = parts[2]       # gpt-5-chat-latest, claude-3-5-sonnet, etc.

                    df = pd.read_csv(csv_file)

                    # Handle Exp3 special format (until-correct experiment)
                    if experiment == 'exp3' and 'kind' in df.columns:
                        # Filter only summary rows
                        df = df[df['kind'] == 'summary'].copy()

                        # Rename columns to match standard format
                        df = df.rename(columns={
                            'type': 'task_type',
                            'pass1': 'pass'
                        })

                        # Calculate aggregated statistics by task type
                        agg_df = df.groupby('task_type').agg({
                            'pass': 'mean',  # Success rate (already 0-1)
                            'attempt_idx': 'mean',  # Average attempts
                            'cumulative_ms': 'mean'  # Average time
                        }).reset_index()

                        agg_df = agg_df.rename(columns={
                            'attempt_idx': 'avg_attempts',
                            'cumulative_ms': 'avg_e2e_ms'
                        })
                        # Keep 'pass' as is (0-1 range)

                        # Add metadata
                        agg_df['experiment'] = experiment
                        agg_df['provider'] = provider
                        agg_df['model'] = model
                        agg_df['provider_model'] = f"{provider}/{model}"
                        agg_df['n'] = df.groupby('task_type').size().values

                        all_results.append(agg_df)
                        print(f"[LOADED] {experiment}/{provider}/{model} ({len(agg_df)} task types, converted from Exp3 format)")
                    else:
                        # Standard format for Exp1/2/4
                        # Rename 'type' to 'task_type' if needed
                        if 'type' in df.columns and 'task_type' not in df.columns:
                            df = df.rename(columns={'type': 'task_type'})

                        # Rename 'pass_at_1' to 'pass' if needed for consistency
                        if 'pass_at_1' in df.columns and 'pass' not in df.columns:
                            df = df.rename(columns={'pass_at_1': 'pass'})

                        df['experiment'] = experiment
                        df['provider'] = provider
                        df['model'] = model
                        df['provider_model'] = f"{provider}/{model}"

                        all_results.append(df)
                        print(f"[LOADED] {experiment}/{provider}/{model} ({len(df)} records)")
            except Exception as e:
                print(f"[SKIP] File {csv_file}: {e}")

        if not all_results:
            print("[ERROR] No result data found")
            return pd.DataFrame()

        combined = pd.concat(all_results, ignore_index=True)
        print(f"\n[SUMMARY] Loaded {len(combined)} records, {len(combined['task_type'].unique())} task types")
        print(f"  Experiments: {sorted(combined['experiment'].unique())}")
        print(f"  Models: {sorted(combined['provider_model'].unique())}")

        return combined

    def _get_accuracy_pivot(self, experiment: str = 'exp1',
                            metric: str = 'pass') -> pd.DataFrame:
        """
        Get accuracy pivot table

        Args:
            experiment: Experiment name (exp1, exp2, exp3, exp4, 'all' for all)
            metric: Metric name (pass, attempts, time, etc.)

        Returns:
            Pivot table with task_type as rows, provider_model as columns
        """
        if self.data.empty:
            return pd.DataFrame()

        # Filter experiment
        if experiment == 'all':
            df = self.data.copy()
        else:
            df = self.data[self.data['experiment'] == experiment].copy()

        if df.empty:
            print(f"[WARNING] Experiment {experiment} has no data")
            return pd.DataFrame()

        # Create pivot table
        pivot = df.pivot_table(
            values=metric,
            index='task_type',
            columns='provider_model',
            aggfunc='mean'
        )

        # Convert to percentage
        if metric == 'pass':
            pivot = pivot * 100

        return pivot

    def plot_heatmap(self, experiment: str = 'exp1',
                     figsize: Tuple[int, int] = (14, 10),
                     save_path: Optional[str] = None):
        """
        Plot heatmap: Task difficulty overview

        Args:
            experiment: Experiment name
            figsize: Figure size
            save_path: Save path (None=don't save)
        """
        pivot = self._get_accuracy_pivot(experiment)

        if pivot.empty:
            print(f"[WARNING] Cannot plot heatmap: {experiment} has no data")
            return None

        # Add average difficulty column
        pivot['Average'] = pivot.mean(axis=1)

        # Sort by average difficulty (hardest at top)
        pivot = pivot.sort_values('Average')

        # Plot heatmap
        fig, ax = plt.subplots(figsize=figsize)

        # Use reverse color scheme (red=hard, green=easy)
        sns.heatmap(
            pivot,
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            vmin=0,
            vmax=100,
            cbar_kws={'label': 'Accuracy (%)'},
            linewidths=0.5,
            linecolor='gray',
            ax=ax,
            mask=pivot.isna(),  # Automatically handle missing values
            cbar=True
        )

        # Title and labels
        exp_title = {
            'exp1': 'Baseline (Ground Truth Prompts)',
            'exp2': 'Optimized Prompts',
            'exp3': 'Until Correct',
            'exp4': 'Few-shot Learning'
        }.get(experiment, experiment)

        ax.set_title(f'CAPTCHA Task Difficulty Heatmap - {exp_title}',
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Model', fontsize=13, fontweight='bold')
        ax.set_ylabel('Task Type (Sorted by Difficulty)', fontsize=13, fontweight='bold')

        # Highlight recommended CAPTCHA zone (accuracy < 60%)
        for i, (task, row) in enumerate(pivot.iterrows()):
            if row['Average'] < 60:
                ax.add_patch(plt.Rectangle((len(pivot.columns)-1, i), 1, 1,
                                          fill=False, edgecolor='red', lw=3))

        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()

        if save_path:
            # Ensure output directory exists
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Heatmap saved: {save_path}")

        return fig

    def plot_comparison_bars(self, experiments: List[str] = ['exp1', 'exp2', 'exp4'],
                            model_filter: Optional[str] = None,
                            figsize: Tuple[int, int] = (18, 7),
                            save_path: Optional[str] = None):
        """
        Plot grouped bar chart: Optimization effect comparison

        Args:
            experiments: List of experiments to compare
            model_filter: Only show specific model (e.g., "openai/gpt-5-chat-latest")
            figsize: Figure size
            save_path: Save path
        """
        if self.data.empty:
            print("[WARNING] Cannot plot bar chart: No data")
            return None

        # Filter data
        df = self.data[self.data['experiment'].isin(experiments)].copy()
        if model_filter:
            df = df[df['provider_model'] == model_filter]

        if df.empty:
            print("[WARNING] No data after filtering")
            return None

        # Calculate average accuracy for each task type in each experiment
        grouped = df.groupby(['task_type', 'experiment'])['pass'].mean() * 100
        pivot = grouped.unstack(fill_value=np.nan)

        # Sort by difficulty of first experiment
        if experiments[0] in pivot.columns:
            pivot = pivot.sort_values(experiments[0])

        # Plot grouped bar chart
        fig, ax = plt.subplots(figsize=figsize)

        x = np.arange(len(pivot))
        width = 0.8 / len(experiments)
        colors = ['#7eb3d6', '#2e75b6', '#70ad47', '#ffc000']

        for i, exp in enumerate(experiments):
            if exp in pivot.columns:
                offset = (i - len(experiments)/2) * width + width/2
                bars = ax.bar(x + offset, pivot[exp], width,
                             label=exp.upper(), color=colors[i % len(colors)],
                             alpha=0.9)

                # Add value labels on bars (only for valid data)
                for j, (idx, val) in enumerate(pivot[exp].items()):
                    if not np.isnan(val):
                        ax.text(x[j] + offset, val + 2, f'{val:.0f}',
                               ha='center', va='bottom', fontsize=8)

        # Add CAPTCHA recommendation threshold line
        ax.axhline(y=60, color='red', linestyle='--', linewidth=2,
                  label='CAPTCHA Threshold (60%)', alpha=0.7)

        ax.set_ylabel('Accuracy (%)', fontsize=13, fontweight='bold')
        ax.set_xlabel('Task Type (Sorted by Difficulty)', fontsize=13, fontweight='bold')

        title = 'Optimization Impact on CAPTCHA Task Difficulty'
        if model_filter:
            title += f'\nModel: {model_filter}'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        ax.set_xticks(x)
        ax.set_xticklabels(pivot.index, rotation=45, ha='right')
        ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
        ax.set_ylim(0, 110)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save_path:
            # Ensure output directory exists
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Bar chart saved: {save_path}")

        return fig

    def plot_optimization_resistance(self, base_exp: str = 'exp1',
                                    opt_exp: str = 'exp2',
                                    model_filter: Optional[str] = None,
                                    figsize: Tuple[int, int] = (11, 11),
                                    save_path: Optional[str] = None):
        """
        Plot scatter plot: Optimization resistance analysis

        Args:
            base_exp: Baseline experiment
            opt_exp: Optimized experiment
            model_filter: Only show specific model
            figsize: Figure size
            save_path: Save path
        """
        if self.data.empty:
            print("[WARNING] Cannot plot scatter plot: No data")
            return None

        # Get data from both experiments
        df = self.data.copy()
        if model_filter:
            df = df[df['provider_model'] == model_filter]

        base_data = df[df['experiment'] == base_exp].groupby('task_type')['pass'].mean() * 100
        opt_data = df[df['experiment'] == opt_exp].groupby('task_type')['pass'].mean() * 100

        # Merge data
        comparison = pd.DataFrame({
            'baseline': base_data,
            'optimized': opt_data
        }).dropna()

        if comparison.empty:
            print(f"[WARNING] {base_exp} and {opt_exp} have no overlapping task types")
            return None

        # Plot scatter plot
        fig, ax = plt.subplots(figsize=figsize)

        # Assign colors based on position
        colors = []
        for idx, row in comparison.iterrows():
            if row['baseline'] < 60 and row['optimized'] < 60:
                colors.append('#d32f2f')  # Red: Recommended CAPTCHA zone
            elif row['baseline'] < 60 and row['optimized'] >= 60:
                colors.append('#ffa726')  # Orange: Significant improvement
            elif row['baseline'] >= 60 and row['optimized'] < 60:
                colors.append('#7e57c2')  # Purple: Abnormal degradation
            else:
                colors.append('#78909c')  # Gray: Easy task type

        # Plot scatter points
        scatter = ax.scatter(comparison['baseline'], comparison['optimized'],
                           s=200, c=colors, alpha=0.7, edgecolors='black', linewidth=1.5)

        # Add task type labels
        for idx, row in comparison.iterrows():
            ax.annotate(idx, (row['baseline'], row['optimized']),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=9, alpha=0.8)

        # Diagonal line (y=x)
        lims = [0, 105]
        ax.plot(lims, lims, 'k--', alpha=0.4, linewidth=1.5, label='No Change (y=x)')

        # CAPTCHA recommendation zone (red box)
        ax.axhline(y=60, color='red', linestyle='--', linewidth=2, alpha=0.5)
        ax.axvline(x=60, color='red', linestyle='--', linewidth=2, alpha=0.5)
        ax.fill_between([0, 60], 0, 60, alpha=0.1, color='red',
                       label='Recommended CAPTCHA Zone')

        # Labels and title
        ax.set_xlabel(f'{base_exp.upper()} Baseline Accuracy (%)',
                     fontsize=13, fontweight='bold')
        ax.set_ylabel(f'{opt_exp.upper()} Optimized Accuracy (%)',
                     fontsize=13, fontweight='bold')

        title = 'Task Optimization Resistance Analysis'
        if model_filter:
            title += f'\nModel: {model_filter}'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.grid(alpha=0.3)
        ax.legend(loc='upper left', fontsize=11, framealpha=0.9)

        # Add legend explanation
        legend_elements = [
            plt.scatter([], [], s=100, c='#d32f2f', alpha=0.7,
                       edgecolors='black', label='Robust (Low -> Low) [RECOMMENDED]'),
            plt.scatter([], [], s=100, c='#ffa726', alpha=0.7,
                       edgecolors='black', label='Improved (Low -> High)'),
            plt.scatter([], [], s=100, c='#78909c', alpha=0.7,
                       edgecolors='black', label='Easy (High -> High)')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

        plt.tight_layout()

        if save_path:
            # Ensure output directory exists
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Scatter plot saved: {save_path}")

        return fig

    def plot_cross_model_stability(self, experiment: str = 'exp1',
                                   figsize: Tuple[int, int] = (16, 8),
                                   save_path: Optional[str] = None):
        """
        Plot box plot: Cross-model stability analysis

        Args:
            experiment: Experiment name
            figsize: Figure size
            save_path: Save path
        """
        if self.data.empty:
            print("[WARNING] Cannot plot box plot: No data")
            return None

        # Filter experiment data
        df = self.data[self.data['experiment'] == experiment].copy()
        if df.empty:
            print(f"[WARNING] Experiment {experiment} has no data")
            return None

        # Calculate statistics for each task type
        df['accuracy'] = df['pass'] * 100

        # Sort task types by median
        median_acc = df.groupby('task_type')['accuracy'].median().sort_values()
        sorted_tasks = median_acc.index.tolist()

        # Plot box plot
        fig, ax = plt.subplots(figsize=figsize)

        # Prepare data
        data_to_plot = [df[df['task_type'] == task]['accuracy'].values
                       for task in sorted_tasks]

        # Set colors based on median
        colors = ['#ef5350' if median_acc[task] < 60 else '#90a4ae'
                 for task in sorted_tasks]

        bp = ax.boxplot(data_to_plot,
                       labels=sorted_tasks,
                       patch_artist=True,
                       widths=0.6,
                       showmeans=True,
                       meanprops=dict(marker='D', markerfacecolor='yellow',
                                    markersize=6, markeredgecolor='black'))

        # Set box colors
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        # CAPTCHA threshold line
        ax.axhline(y=60, color='red', linestyle='--', linewidth=2,
                  label='CAPTCHA Threshold', alpha=0.7)

        ax.set_ylabel('Accuracy (%) across Models', fontsize=13, fontweight='bold')
        ax.set_xlabel('Task Type (Sorted by Median Difficulty)',
                     fontsize=13, fontweight='bold')
        ax.set_title(f'Cross-Model Stability Analysis - {experiment.upper()}',
                    fontsize=16, fontweight='bold', pad=20)

        plt.xticks(rotation=45, ha='right')
        ax.set_ylim(-5, 105)
        ax.grid(axis='y', alpha=0.3)
        ax.legend(fontsize=11)

        plt.tight_layout()

        if save_path:
            # Ensure output directory exists
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Box plot saved: {save_path}")

        return fig

    def generate_captcha_recommendation(self, experiment: str = 'exp2',
                                       threshold: float = 60.0,
                                       top_n: int = 8) -> pd.DataFrame:
        """
        Generate CAPTCHA recommended task type list

        Args:
            experiment: Experiment for evaluation
            threshold: CAPTCHA recommendation threshold
            top_n: Return top N hardest task types

        Returns:
            Recommended task types DataFrame
        """
        if self.data.empty:
            print("[WARNING] No data")
            return pd.DataFrame()

        # Get experiment data
        df = self.data[self.data['experiment'] == experiment].copy()

        # Calculate statistics for each task type
        stats = df.groupby('task_type').agg({
            'pass': ['mean', 'std', 'count']
        }).round(4)

        stats.columns = ['avg_accuracy', 'std_accuracy', 'n_models']
        stats['avg_accuracy'] *= 100
        stats['std_accuracy'] *= 100

        # Filter difficult task types
        difficult_tasks = stats[stats['avg_accuracy'] < threshold].copy()
        difficult_tasks = difficult_tasks.sort_values('avg_accuracy')

        # Add recommendation score
        difficult_tasks['captcha_score'] = (
            (100 - difficult_tasks['avg_accuracy']) * 0.6 +  # Difficulty weight
            (100 - difficult_tasks['std_accuracy']) * 0.4     # Stability weight
        )

        difficult_tasks = difficult_tasks.sort_values('captcha_score', ascending=False)

        result = difficult_tasks.head(top_n).copy()
        result['rank'] = range(1, len(result) + 1)

        return result[['rank', 'avg_accuracy', 'std_accuracy', 'n_models', 'captcha_score']]

    def plot_all(self, output_dir: str = "./figures"):
        """
        Generate all charts and save

        Args:
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        print(f"\nGenerating charts, saving to: {output_dir}/\n")

        # Detect available experiments
        available_exps = sorted(self.data['experiment'].unique()) if not self.data.empty else []
        available_models = sorted(self.data['provider_model'].unique()) if not self.data.empty else []

        print(f"[DETECTED] Experiments: {available_exps}")
        print(f"[DETECTED] Models: {available_models}\n")

        figures = []

        # 1. Heatmap (for each experiment)
        for exp in available_exps:
            try:
                fig = self.plot_heatmap(
                    experiment=exp,
                    save_path=str(output_path / f"heatmap_{exp}.pdf")
                )
                if fig:
                    figures.append(fig)
                    plt.close(fig)
            except Exception as e:
                print(f"[WARNING] Heatmap {exp} generation failed: {e}")

        # 2. Grouped bar chart (compare experiments)
        if len(available_exps) >= 2:
            for model in available_models:
                try:
                    fig = self.plot_comparison_bars(
                        experiments=available_exps,
                        model_filter=model,
                        save_path=str(output_path / f"comparison_{model.replace('/', '_')}.pdf")
                    )
                    if fig:
                        figures.append(fig)
                        plt.close(fig)
                except Exception as e:
                    print(f"[WARNING] Bar chart {model} generation failed: {e}")

        # 3. Scatter plot (exp1 vs exp2)
        if 'exp1' in available_exps and 'exp2' in available_exps:
            for model in available_models:
                try:
                    fig = self.plot_optimization_resistance(
                        base_exp='exp1',
                        opt_exp='exp2',
                        model_filter=model,
                        save_path=str(output_path / f"resistance_{model.replace('/', '_')}.pdf")
                    )
                    if fig:
                        figures.append(fig)
                        plt.close(fig)
                except Exception as e:
                    print(f"[WARNING] Scatter plot {model} generation failed: {e}")

        # 4. Box plot (cross-model stability)
        for exp in available_exps:
            if len(self.data[self.data['experiment'] == exp]['provider_model'].unique()) >= 2:
                try:
                    fig = self.plot_cross_model_stability(
                        experiment=exp,
                        save_path=str(output_path / f"stability_{exp}.pdf")
                    )
                    if fig:
                        figures.append(fig)
                        plt.close(fig)
                except Exception as e:
                    print(f"[WARNING] Box plot {exp} generation failed: {e}")

        print(f"\n[COMPLETED] Chart generation finished! Total {len(list(output_path.glob('*.pdf')))} PDF files")
        print(f"[OUTPUT] Save location: {output_path.absolute()}")

        return figures


# ============================================================================
# Convenience Functions
# ============================================================================

def quick_visualize(results_dir: str = "./results",
                   output_dir: str = "./figures",
                   show: bool = False):
    """
    Quickly generate all visualization charts

    Args:
        results_dir: Results directory
        output_dir: Output directory
        show: Whether to display charts (recommend False in Jupyter)
    """
    viz = CAPTCHAVisualizer(results_dir=results_dir)

    if viz.data.empty:
        print("[ERROR] No experiment data found")
        return None

    # Generate all charts
    viz.plot_all(output_dir=output_dir)

    # Generate recommendation report
    print("\n" + "="*60)
    print("CAPTCHA Recommended Task Types (Based on Exp2 Optimized Results)")
    print("="*60)

    if 'exp2' in viz.data['experiment'].values:
        recommendations = viz.generate_captcha_recommendation(
            experiment='exp2',
            threshold=60.0,
            top_n=8
        )
        if not recommendations.empty:
            print(recommendations.to_string())

            # Save recommendation list
            rec_path = Path(output_dir) / "captcha_recommendations.csv"
            recommendations.to_csv(rec_path)
            print(f"\n[SAVED] Recommendation list saved: {rec_path}")
    else:
        print("[WARNING] Exp2 not run yet, cannot generate recommendations")

    print("\n[COMPLETED] Visualization finished!")

    if not show:
        plt.close('all')

    return viz


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Quickly generate all charts
    viz = quick_visualize(
        results_dir="./results",
        output_dir="./figures",
        show=False
    )
