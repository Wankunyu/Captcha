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

# Optional dependency to avoid overlapping text labels in scatter plots
try:
    from adjustText import adjust_text  # type: ignore
except Exception:
    adjust_text = None

# Set font and chart style
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")

class CAPTCHAVisualizer:
    """CAPTCHA experiment result visualizer"""

    # Default model display name mapping
    DEFAULT_MODEL_NAMES = {
        'openai/gpt-5': 'GPT-5',
        'openai/gpt-5-chat-latest': 'GPT-5-Chat',
        'openai/gpt-5.1_medium': 'GPT-5.1 (Medium)',
        'openai/gpt-5.1_none': 'GPT-5.1 (None)',
        'anthropic/claude-sonnet-4-5': 'Claude Sonnet 4.5',
        'anthropic/claude-3-5-sonnet-20241022': 'Claude 3.5 Sonnet',
        'gemini/gemini-2.5-flash': 'Gemini 2.5 Flash',
        'gemini/gemini-2.5-pro': 'Gemini 2.5 Pro',
        'fireworks/accounts_fireworks_models_qwen3-vl-235b-a22b-instruct': 'Qwen3-VL-235B',
    }

    # Default experiment display name mapping
    DEFAULT_EXP_NAMES = {
        'exp1': 'Exp1 (Baseline)',
        'exp2': 'Exp2 (Optimized)',
        'exp3': 'Exp3 (Until-Correct)',
        'exp4': 'Exp4 (Few-Shot)',
    }

    # Task family (category) mapping for radar plots and grouped summaries
    TASK_FAMILY = {
        # Click / Coordinate tasks
        'Dice_Count': 'Click/Coordinate',
        'Click_Order': 'Click/Coordinate',
        'Place_Dot': 'Click/Coordinate',
        'Geometry_Click': 'Click/Coordinate',
        'Pick_Area': 'Click/Coordinate',
        'Misleading_Click': 'Click/Coordinate',

        # Grid selection
        'Patch_Select': 'Grid Selection',
        'Select_Animal': 'Grid Selection',
        'Image_Recognition': 'Grid Selection',
        'Unusual_Detection': 'Grid Selection',

        # Image matching
        'Image_Matching': 'Image Matching',
        'Object_Match': 'Image Matching',
        'Path_Finder': 'Image Matching',
        'Rotation_Match': 'Image Matching',

        # Logic / Reasoning
        'Bingo': 'Logic/Reasoning',
        'Dart_Count': 'Logic/Reasoning',
        'Coordinates': 'Logic/Reasoning',
        'Connect_Icon': 'Logic/Reasoning',
    }

    def __init__(self, results_dir: str = "./results", error_dir: str = "./error_analysis",
                 model_names: Optional[Dict[str, str]] = None,
                 exp_names: Optional[Dict[str, str]] = None):
        """
        Initialize CAPTCHA visualizer

        Args:
            results_dir: Results directory path
            error_dir: Error analysis directory path
            model_names: Custom model display names (overrides defaults)
            exp_names: Custom experiment display names (overrides defaults)
        """
        self.results_dir = Path(results_dir)
        self.error_dir = Path(error_dir)

        # Merge custom names with defaults
        self.model_names = self.DEFAULT_MODEL_NAMES.copy()
        if model_names:
            self.model_names.update(model_names)

        self.exp_names = self.DEFAULT_EXP_NAMES.copy()
        if exp_names:
            self.exp_names.update(exp_names)

        self.data = self._load_all_data()
        self.task_types = sorted(self.data['task_type'].unique()) if not self.data.empty else []

    def _get_display_name(self, identifier: str, name_type: str = 'model') -> str:
        """
        Get display name for model or experiment

        Args:
            identifier: Original identifier (e.g., 'openai/gpt-5')
            name_type: 'model' or 'experiment'

        Returns:
            Display name or original identifier if not found
        """
        if name_type == 'model':
            return self.model_names.get(identifier, identifier)
        elif name_type == 'experiment':
            return self.exp_names.get(identifier, identifier)
        return identifier

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

                        # Prepare per-row metrics before grouping (each summary row = one task type per run)
                        import numpy as _np
                        eps = 1e-9
                        df['avg_attempts_per_row'] = df['attempt_idx']
                        df['cum_e2e_ms_per_row'] = df['cumulative_ms']
                        df['avg_e2e_ms_per_row'] = df['cumulative_ms'] / _np.clip(df['attempt_idx'], eps, None)

                        # Aggregate statistics by task type (mean across runs if multiple exist)
                        agg_df = df.groupby('task_type').agg({
                            'pass': 'mean',
                            'avg_attempts_per_row': 'mean',
                            'cum_e2e_ms_per_row': 'mean',
                            'avg_e2e_ms_per_row': 'mean'
                        }).reset_index()

                        agg_df = agg_df.rename(columns={
                            'avg_attempts_per_row': 'avg_attempts',
                            'cum_e2e_ms_per_row': 'cum_e2e_ms',
                            'avg_e2e_ms_per_row': 'avg_e2e_ms'
                        })

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

        # Rename columns to display names
        pivot.columns = [self._get_display_name(col, 'model') for col in pivot.columns]

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
            cbar_kws={'label': 'Pass@1 (%)'},
            linewidths=0.5,
            linecolor='gray',
            ax=ax,
            mask=pivot.isna(),  # Automatically handle missing values
            cbar=True
        )

        # Title and labels
        exp_title = self._get_display_name(experiment, 'experiment')

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

    def plot_cost_performance_frontier(self,
                                       experiments: List[str] = ('exp1', 'exp2', 'exp4'),
                                       model_filter: Optional[str] = None,
                                       log_x: bool = True,
                                       figsize: Tuple[int, int] = (12, 8),
                                       save_path: Optional[str] = None):
        """
        Cost–Performance frontier: x=cost_per_question (USD), y=Pass@1 (%).
        Overlays multiple experiments for the same model.
        """
        if self.data.empty:
            print("[WARNING] Cannot plot frontier: No data")
            return None

        df = self.data.copy()
        if model_filter:
            df = df[df['provider_model'] == model_filter]
        df = df[df['experiment'].isin(experiments)]
        if df.empty:
            print("[WARNING] No data after filtering for frontier plot")
            return None

        # Require cost column
        if 'cost_per_question' not in df.columns:
            print("[WARNING] results.csv missing cost_per_question column; skip frontier plot")
            return None

        # Prepare figure
        fig, ax = plt.subplots(figsize=figsize)

        colors = ['#2e75b6', '#70ad47', '#ffc000', '#d32f2f']
        exp_list = [e for e in experiments if e in set(df['experiment'])]
        for i, exp in enumerate(exp_list):
            sub = df[df['experiment'] == exp].copy()
            if sub.empty:
                continue
            sub['pass_pct'] = sub['pass'] * 100
            ax.scatter(sub['cost_per_question'], sub['pass_pct'],
                       s=80, alpha=0.8, label=self._get_display_name(exp, 'experiment'),
                       color=colors[i % len(colors)], edgecolors='black', linewidths=0.8)

            # Optional: simple Pareto frontier (maximize y, minimize x)
            pts = sub[['cost_per_question', 'pass_pct']].dropna().values
            if len(pts) >= 2:
                # Sort by cost asc, then sweep to keep increasing pass
                pts_sorted = pts[pts[:, 0].argsort()]
                frontier = []
                best_y = -1
                for x, y in pts_sorted:
                    if y > best_y:
                        frontier.append((x, y))
                        best_y = y
                if len(frontier) >= 2:
                    xs, ys = zip(*frontier)
                    ax.plot(xs, ys, color=colors[i % len(colors)], linestyle='-', alpha=0.6)

        ax.axhline(y=60, color='red', linestyle='--', linewidth=2, alpha=0.5, label='CAPTCHA Threshold (60%)')
        ax.set_ylabel('Pass@1 (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Cost per Question (USD)', fontsize=12, fontweight='bold')
        ax.set_ylim(-5, 105)
        if log_x:
            ax.set_xscale('log')
        ax.grid(alpha=0.3, which='both', axis='both')

        title = 'Cost–Performance Frontier'
        if model_filter:
            title += f"\nModel: {self._get_display_name(model_filter, 'model')}"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=16)
        ax.legend(loc='lower right', fontsize=10, framealpha=0.9)

        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Frontier saved: {save_path}")
        return fig

    def plot_time_performance_scatter(self,
                                       experiments: List[str] = ('exp1', 'exp2', 'exp3', 'exp4'),
                                       model_filter: Optional[str] = None,
                                       metric: str = 'avg_e2e_ms',
                                       figsize: Tuple[int, int] = (12, 8),
                                       save_path: Optional[str] = None):
        """
        Time–Performance scatter: x=avg_e2e_ms, y=Pass@1 (%). Overlays experiments.
        """
        if self.data.empty:
            print("[WARNING] Cannot plot time-performance: No data")
            return None

        if metric not in self.data.columns:
            print(f"[WARNING] Column '{metric}' not found; skip time-performance plot")
            return None

        df = self.data.copy()
        if model_filter:
            df = df[df['provider_model'] == model_filter]
        df = df[df['experiment'].isin(experiments)]
        if df.empty:
            print("[WARNING] No data after filtering for time-performance plot")
            return None

        fig, ax = plt.subplots(figsize=figsize)
        colors = ['#7eb3d6', '#2e75b6', '#70ad47', '#ffc000']
        exp_list = [e for e in experiments if e in set(df['experiment'])]

        for i, exp in enumerate(exp_list):
            sub = df[df['experiment'] == exp].copy()
            if sub.empty:
                continue
            sub = sub.dropna(subset=[metric])
            sub['pass_pct'] = sub['pass'] * 100
            # Convert milliseconds to seconds for unified units (s)
            ax.scatter(sub[metric] / 1000.0, sub['pass_pct'], s=80, alpha=0.85,
                       label=self._get_display_name(exp, 'experiment'),
                       color=colors[i % len(colors)], edgecolors='black', linewidths=0.8)

        ax.axhline(y=60, color='red', linestyle='--', linewidth=2, alpha=0.5)
        ax.set_ylabel('Pass@1 (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Average E2E Time (s)', fontsize=12, fontweight='bold')
        ax.set_ylim(-5, 105)
        ax.grid(alpha=0.3)

        title = 'Time–Performance Scatter'
        if model_filter:
            title += f"\nModel: {self._get_display_name(model_filter, 'model')}"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=16)
        ax.legend(loc='lower left', fontsize=10, framealpha=0.9)

        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Time–Performance saved: {save_path}")
        return fig

    def plot_slope_improvement(self,
                               base_exp: str = 'exp1',
                               target_exp: str = 'exp2',
                               model_filter: Optional[str] = None,
                               top_k: Optional[int] = None,
                               figsize: Tuple[int, int] = (16, 8),
                               save_path: Optional[str] = None):
        """
        Slope chart: per-task change from base_exp to target_exp.
        """
        if self.data.empty:
            print("[WARNING] Cannot plot slope: No data")
            return None

        df = self.data.copy()
        if model_filter:
            df = df[df['provider_model'] == model_filter]

        a = df[df['experiment'] == base_exp].groupby('task_type')['pass'].mean()
        b = df[df['experiment'] == target_exp].groupby('task_type')['pass'].mean()

        merged = pd.DataFrame({'base': a, 'target': b}).dropna()
        if merged.empty:
            print("[WARNING] No overlapping tasks for slope plot")
            return None

        merged['base_pct'] = merged['base'] * 100
        merged['target_pct'] = merged['target'] * 100
        merged['delta'] = merged['target_pct'] - merged['base_pct']
        merged = merged.sort_values('base_pct')

        if top_k and top_k > 0:
            # Select top_k with largest absolute improvement
            sel = merged.reindex(merged['delta'].abs().sort_values(ascending=False).index).head(top_k)
            merged = merged.loc[sel.index]

        fig, ax = plt.subplots(figsize=figsize)
        x = np.arange(len(merged))
        ax.scatter(x, merged['base_pct'], color='#7eb3d6', label=self._get_display_name(base_exp, 'experiment'))
        ax.scatter(x, merged['target_pct'], color='#70ad47', label=self._get_display_name(target_exp, 'experiment'))
        for i, (y0, y1) in enumerate(zip(merged['base_pct'], merged['target_pct'])):
            color = '#70ad47' if y1 >= y0 else '#d32f2f'
            ax.plot([i, i], [y0, y1], color=color, linewidth=2, alpha=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(merged.index, rotation=45, ha='right')
        ax.set_ylabel('Pass@1 (%)', fontsize=12, fontweight='bold')
        ax.set_title('Improvement Slope', fontsize=16, fontweight='bold', pad=16)
        if model_filter:
            ax.set_title(f"Improvement Slope\nModel: {self._get_display_name(model_filter, 'model')}", fontsize=16, fontweight='bold', pad=16)
        ax.axhline(y=60, color='red', linestyle='--', linewidth=2, alpha=0.5)
        ax.set_ylim(-5, 105)
        ax.grid(alpha=0.3, axis='y')
        ax.legend(fontsize=10)

        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Slope saved: {save_path}")
        return fig

    def plot_task_family_radar(self,
                                experiment: str = 'exp2',
                                model_filter: Optional[str] = None,
                                figsize: Tuple[int, int] = (8, 8),
                                save_path: Optional[str] = None):
        """
        Radar chart of average Pass@1 by task family (Click/Coordinate, Grid Selection, Image Matching, Logic/Reasoning).
        """
        if self.data.empty:
            print("[WARNING] Cannot plot radar: No data")
            return None

        df = self.data.copy()
        df = df[df['experiment'] == experiment]
        if model_filter:
            df = df[df['provider_model'] == model_filter]
        if df.empty:
            print("[WARNING] No data for radar after filtering")
            return None

        # Map to families
        df['family'] = df['task_type'].map(self.TASK_FAMILY).fillna('Other')
        fam = df.groupby('family')['pass'].mean().reindex(['Click/Coordinate', 'Grid Selection', 'Image Matching', 'Logic/Reasoning']).fillna(0)
        values = (fam * 100).values.tolist()
        labels = fam.index.tolist()
        # Close the polygon
        values += values[:1]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, polar=True)
        ax.plot(angles, values, color='#2e75b6', linewidth=2, zorder=2)
        ax.fill(angles, values, color='#7eb3d6', alpha=0.25, zorder=1)

        # Compute separate angles for label placement (without closing angle)
        label_angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)

        # Hide default theta tick labels and draw custom labels slightly outside the outer ring
        ax.set_xticks([])
        rmax = 110  # extend radius a bit to leave room for labels
        ax.set_ylim(0, rmax)
        label_r = rmax * 0.985
        for a, lab in zip(label_angles, labels):
            # Choose alignment based on quadrant so labels stay outside
            if -np.pi/2 <= a <= np.pi/2:
                ha = 'left'
            elif np.pi/2 < a < 3*np.pi/2:
                ha = 'right'
            else:
                ha = 'center'
            ax.text(a, label_r, lab, ha=ha, va='center', fontsize=11,
                    bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.7),
                    zorder=3)

        # Move radial tick labels away from crowded areas
        ax.set_rlabel_position(225)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'])

        title = f"Task Family Radar - {self._get_display_name(experiment, 'experiment')}"
        if model_filter:
            title += f"\nModel: {self._get_display_name(model_filter, 'model')}"
        ax.set_title(title, fontsize=14, fontweight='bold', va='bottom')

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Radar saved: {save_path}")
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
                exp_label = self._get_display_name(exp, 'experiment')
                bars = ax.bar(x + offset, pivot[exp], width,
                             label=exp_label, color=colors[i % len(colors)],
                             alpha=0.9)

                # Add value labels on bars (only for valid data)
                for j, (idx, val) in enumerate(pivot[exp].items()):
                    if not np.isnan(val):
                        ax.text(x[j] + offset, val + 2, f'{val:.0f}',
                               ha='center', va='bottom', fontsize=8)

        # Add CAPTCHA recommendation threshold line
        ax.axhline(y=60, color='red', linestyle='--', linewidth=2,
                  label='CAPTCHA Threshold (60%)', alpha=0.7)

        ax.set_ylabel('Pass@1 (%)', fontsize=13, fontweight='bold')
        ax.set_xlabel('Task Type (Sorted by Difficulty)', fontsize=13, fontweight='bold')

        title = 'Optimization Impact on CAPTCHA Task Difficulty'
        if model_filter:
            model_display = self._get_display_name(model_filter, 'model')
            title += f'\nModel: {model_display}'
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
                                    save_path: Optional[str] = None,
                                    use_adjust_text: bool = True):
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

        # Add task labels; prefer using adjustText to reduce overlaps if available
        texts = []
        for idx, row in comparison.iterrows():
            t = ax.text(row['baseline'], row['optimized'], idx,
                        fontsize=9, alpha=0.9, color='black')
            texts.append(t)

        if use_adjust_text and adjust_text is not None and len(texts) > 0:
            try:
                adjust_text(
                    texts,
                    ax=ax,
                    only_move={'points': 'y', 'texts': 'xy'},
                    autoalign='y',
                    force_points=0.2,
                    force_text=0.2,
                    expand_text=(1.05, 1.2),
                    expand_points=(1.1, 1.3),
                    arrowprops=dict(arrowstyle='-', color='gray', lw=0.5, alpha=0.6)
                )
            except Exception as e:
                print(f"[WARNING] adjustText failed: {e}. Falling back to static labels.")
        elif use_adjust_text and adjust_text is None:
            print("[INFO] 'adjustText' not installed. Run 'pip install adjustText' to enable automatic label adjustment.")

        # Diagonal line (y=x)
        lims = [0, 105]
        ax.plot(lims, lims, 'k--', alpha=0.4, linewidth=1.5, label='No Change (y=x)')

        # CAPTCHA recommendation zone (red box)
        ax.axhline(y=60, color='red', linestyle='--', linewidth=2, alpha=0.5)
        ax.axvline(x=60, color='red', linestyle='--', linewidth=2, alpha=0.5)
        ax.fill_between([0, 60], 0, 60, alpha=0.1, color='red',
                       label='Recommended CAPTCHA Zone')

        # Labels and title
        base_exp_display = self._get_display_name(base_exp, 'experiment')
        opt_exp_display = self._get_display_name(opt_exp, 'experiment')

        ax.set_xlabel(f'{base_exp_display} Pass@1 (%)',
                     fontsize=13, fontweight='bold')
        ax.set_ylabel(f'{opt_exp_display} Pass@1 (%)',
                     fontsize=13, fontweight='bold')

        title = 'Task Optimization Resistance Analysis'
        if model_filter:
            model_display = self._get_display_name(model_filter, 'model')
            title += f'\nModel: {model_display}'
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
                       edgecolors='black', label='Easy (High -> High)'),
            plt.scatter([], [], s=100, c='#7e57c2', alpha=0.7,
                       edgecolors='black', label='Easy (High -> Low) [ALERT]')
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

        ax.set_ylabel('Pass@1 (%) across Models', fontsize=13, fontweight='bold')
        ax.set_xlabel('Task Type (Sorted by Median Difficulty)',
                     fontsize=13, fontweight='bold')

        exp_display = self._get_display_name(experiment, 'experiment')
        ax.set_title(f'Cross-Model Stability Analysis - {exp_display}',
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

    def plot_exp3_analysis(self, model_filter: Optional[str] = None,
                          figsize: Tuple[int, int] = (20, 12),
                          save_path: Optional[str] = None):
        """
        Plot comprehensive Experiment 3 (Until-Correct) analysis with 4 subplots

        Args:
            model_filter: Only show specific model
            figsize: Figure size
            save_path: Save path

        Returns:
            Figure object
        """
        if self.data.empty:
            print("[WARNING] Cannot plot Exp3 analysis: No data")
            return None

        # Filter Exp3 data
        df = self.data[self.data['experiment'] == 'exp3'].copy()
        if model_filter:
            df = df[df['provider_model'] == model_filter]

        if df.empty:
            print("[WARNING] No Exp3 data available")
            return None

        # Check if required columns exist
        if 'avg_attempts' not in df.columns or 'avg_e2e_ms' not in df.columns:
            print("[WARNING] Exp3 data missing required columns (avg_attempts, avg_e2e_ms)")
            return None

        # Create figure with 4 subplots
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Aggregate by task type (in case multiple runs/files were merged)
        task_stats = df.groupby('task_type').agg({
            'pass': 'mean',
            'avg_attempts': 'mean',
            'avg_e2e_ms': 'mean',   # derived avg per attempt in loader
            'cum_e2e_ms': 'mean',   # cumulative time across attempts
            'n': 'sum'
        }).reset_index()

        task_stats['pass_pct'] = task_stats['pass'] * 100
        # Cumulative time until success (seconds)
        task_stats['cum_time_sec'] = task_stats['cum_e2e_ms'] / 1000.0
        # Average time per attempt (seconds)
        task_stats['avg_time_per_attempt_sec'] = task_stats['avg_e2e_ms'] / 1000.0

        # Sort by average attempts (descending)
        task_stats = task_stats.sort_values('avg_attempts', ascending=False)

        # Color palette
        colors_hard = ['#d32f2f' if x >= 5 else '#7eb3d6' for x in task_stats['avg_attempts']]

        # ===== Subplot 1: Average Attempts per Task Type =====
        ax1 = fig.add_subplot(gs[0, 0])
        bars1 = ax1.barh(task_stats['task_type'], task_stats['avg_attempts'], color=colors_hard, alpha=0.8)
        ax1.set_xlabel('Average Attempts Until Success', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Task Type', fontsize=11, fontweight='bold')
        ax1.set_title('Exp3: Retry Attempts Required', fontsize=13, fontweight='bold')
        ax1.axvline(x=5, color='red', linestyle='--', linewidth=2, alpha=0.5, label='High Difficulty (≥5 attempts)')
        ax1.grid(axis='x', alpha=0.3)
        ax1.legend(fontsize=9)

        # Add value labels
        for i, (idx, row) in enumerate(task_stats.iterrows()):
            ax1.text(row['avg_attempts'] + 0.2, i, f"{row['avg_attempts']:.1f}",
                    va='center', fontsize=9)

        # ===== Subplot 2: Average Time per Task Type =====
        ax2 = fig.add_subplot(gs[0, 1])
        task_stats_time = task_stats.sort_values('cum_time_sec', ascending=False)
        colors_time = ['#ff6b6b' if x >= 30 else '#4ecdc4' for x in task_stats_time['cum_time_sec']]
        bars2 = ax2.barh(task_stats_time['task_type'], task_stats_time['cum_time_sec'], color=colors_time, alpha=0.8)
        ax2.set_xlabel('Cumulative Time Until Success (s)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Task Type', fontsize=11, fontweight='bold')
        ax2.set_title('Exp3: Time Cost Analysis', fontsize=13, fontweight='bold')
        ax2.axvline(x=30, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='High Time Cost (≥30s)')
        ax2.grid(axis='x', alpha=0.3)
        ax2.legend(fontsize=9)

        # Add value labels
        for i, (idx, row) in enumerate(task_stats_time.iterrows()):
            ax2.text(row['cum_time_sec'] + 1, i, f"{row['cum_time_sec']:.1f}s",
                    va='center', fontsize=9)

        # ===== Subplot 3: Pass@1 vs Until-Correct Success Rate =====
        ax3 = fig.add_subplot(gs[1, 0])

        # Get Exp1 data for comparison (Pass@1)
        exp1_data = self.data[self.data['experiment'] == 'exp1'].copy()
        if model_filter:
            exp1_data = exp1_data[exp1_data['provider_model'] == model_filter]

        if not exp1_data.empty:
            exp1_pass = exp1_data.groupby('task_type')['pass'].mean() * 100
            exp3_pass = task_stats.set_index('task_type')['pass_pct']

            # Merge data
            comparison = pd.DataFrame({
                'Pass@1 (Exp1)': exp1_pass,
                'Until-Correct (Exp3)': exp3_pass
            }).fillna(0)

            comparison = comparison.sort_values('Pass@1 (Exp1)')

            x = np.arange(len(comparison))
            width = 0.35

            bars_exp1 = ax3.bar(x - width/2, comparison['Pass@1 (Exp1)'], width,
                               label='Pass@1 (Exp1 Baseline)', color='#7eb3d6', alpha=0.9)
            bars_exp3 = ax3.bar(x + width/2, comparison['Until-Correct (Exp3)'], width,
                               label='Until-Correct (Exp3)', color='#70ad47', alpha=0.9)

            ax3.set_ylabel('Success Rate (%)', fontsize=11, fontweight='bold')
            ax3.set_xlabel('Task Type', fontsize=11, fontweight='bold')
            ax3.set_title('Pass@1 vs Until-Correct Success Rate', fontsize=13, fontweight='bold')
            ax3.set_xticks(x)
            ax3.set_xticklabels(comparison.index, rotation=45, ha='right', fontsize=9)
            ax3.axhline(y=60, color='red', linestyle='--', linewidth=2, alpha=0.5)
            ax3.legend(fontsize=10)
            ax3.grid(axis='y', alpha=0.3)
            ax3.set_ylim(0, 110)
        else:
            ax3.text(0.5, 0.5, 'Exp1 data not available for comparison',
                    ha='center', va='center', fontsize=12, transform=ax3.transAxes)
            ax3.set_title('Pass@1 vs Until-Correct Success Rate', fontsize=13, fontweight='bold')

        # ===== Subplot 4: Time Efficiency (Time per Attempt) =====
        ax4 = fig.add_subplot(gs[1, 1])
        task_stats_eff = task_stats.sort_values('avg_time_per_attempt_sec', ascending=False)
        colors_eff = ['#9b59b6' if x >= 5 else '#95a5a6' for x in task_stats_eff['avg_time_per_attempt_sec']]
        bars4 = ax4.barh(task_stats_eff['task_type'], task_stats_eff['avg_time_per_attempt_sec'], color=colors_eff, alpha=0.8)
        ax4.set_xlabel('Average Time per Attempt (s)', fontsize=11, fontweight='bold')
        ax4.set_ylabel('Task Type', fontsize=11, fontweight='bold')
        ax4.set_title('Exp3: Time Efficiency per Attempt', fontsize=13, fontweight='bold')
        ax4.axvline(x=5, color='purple', linestyle='--', linewidth=2, alpha=0.5, label='Slow (≥5s/attempt)')
        ax4.grid(axis='x', alpha=0.3)
        ax4.legend(fontsize=9)

        # Add value labels
        for i, (idx, row) in enumerate(task_stats_eff.iterrows()):
            ax4.text(row['avg_time_per_attempt_sec'] + 0.2, i, f"{row['avg_time_per_attempt_sec']:.1f}s",
                    va='center', fontsize=9)

        # Main title
        exp3_display = self._get_display_name('exp3', 'experiment')
        title = f'{exp3_display} Comprehensive Analysis'
        if model_filter:
            model_display = self._get_display_name(model_filter, 'model')
            title += f'\nModel: {model_display}'
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.995)

        if save_path:
            # Ensure output directory exists
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, format='pdf', bbox_inches='tight')
            print(f"[SAVED] Exp3 analysis saved: {save_path}")

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

        stats.columns = ['avg_pass@1', 'std_pass@1', 'n_models']
        stats['avg_pass@1'] *= 100
        stats['std_pass@1'] *= 100

        # Filter difficult task types
        difficult_tasks = stats[stats['avg_pass@1'] < threshold].copy()
        difficult_tasks = difficult_tasks.sort_values('avg_pass@1')

        # Add recommendation score
        difficult_tasks['captcha_score'] = (
            (100 - difficult_tasks['avg_pass@1']) * 0.6 +  # Difficulty weight
            (100 - difficult_tasks['std_pass@1']) * 0.4     # Stability weight
        )

        difficult_tasks = difficult_tasks.sort_values('captcha_score', ascending=False)

        result = difficult_tasks.head(top_n).copy()
        result['rank'] = range(1, len(result) + 1)

        return result[['rank', 'avg_pass@1', 'std_pass@1', 'n_models', 'captcha_score']]

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

        # 5. Exp3 comprehensive analysis (if available)
        if 'exp3' in available_exps:
            for model in available_models:
                try:
                    fig = self.plot_exp3_analysis(
                        model_filter=model,
                        save_path=str(output_path / f"exp3_analysis_{model.replace('/', '_')}.pdf")
                    )
                    if fig:
                        figures.append(fig)
                        plt.close(fig)
                except Exception as e:
                    print(f"[WARNING] Exp3 analysis {model} generation failed: {e}")

        # 6. Cost–Performance frontier per model (if cost columns present)
        for model in available_models:
            try:
                fig = self.plot_cost_performance_frontier(
                    experiments=[e for e in available_exps if e in ('exp1', 'exp2', 'exp4')],
                    model_filter=model,
                    save_path=str(output_path / f"frontier_{model.replace('/', '_')}.pdf")
                )
                if fig:
                    figures.append(fig)
                    plt.close(fig)
            except Exception as e:
                print(f"[WARNING] Frontier {model} generation failed: {e}")

        # 7. Time–Performance scatter per model
        for model in available_models:
            try:
                fig = self.plot_time_performance_scatter(
                    experiments=available_exps,
                    model_filter=model,
                    save_path=str(output_path / f"time_perf_{model.replace('/', '_')}.pdf")
                )
                if fig:
                    figures.append(fig)
                    plt.close(fig)
            except Exception as e:
                print(f"[WARNING] Time–Performance {model} generation failed: {e}")

        # 8. Slope improvement (exp1→exp2) per model if both exist
        if 'exp1' in available_exps and 'exp2' in available_exps:
            for model in available_models:
                try:
                    fig = self.plot_slope_improvement(
                        base_exp='exp1', target_exp='exp2', model_filter=model,
                        save_path=str(output_path / f"slope_exp1_to_exp2_{model.replace('/', '_')}.pdf")
                    )
                    if fig:
                        figures.append(fig)
                        plt.close(fig)
                except Exception as e:
                    print(f"[WARNING] Slope {model} generation failed: {e}")

        # 9. Radar (by task family) for exp2 per model (fallback to exp1)
        target_exp_for_radar = 'exp2' if 'exp2' in available_exps else ('exp1' if 'exp1' in available_exps else None)
        if target_exp_for_radar:
            for model in available_models:
                try:
                    fig = self.plot_task_family_radar(
                        experiment=target_exp_for_radar,
                        model_filter=model,
                        save_path=str(output_path / f"radar_{target_exp_for_radar}_{model.replace('/', '_')}.pdf")
                    )
                    if fig:
                        figures.append(fig)
                        plt.close(fig)
                except Exception as e:
                    print(f"[WARNING] Radar {model} generation failed: {e}")

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
