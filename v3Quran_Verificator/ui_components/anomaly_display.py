"""
Enhanced Anomaly Display Component
Provides detailed anomaly visualization and explanation
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class AnomalyDisplay:
    """Advanced anomaly display with visual highlighting and explanations"""
    
    def __init__(self):
        self.anomaly_colors = {
            'high': '#FF4444',      # Red for high severity
            'medium': '#FF8800',    # Orange for medium severity
            'low': '#FFDD00',       # Yellow for low severity
            'info': '#0088FF'       # Blue for informational
        }
    
    def display_anomaly_summary(self, verification_results: Dict) -> None:
        """Display overall anomaly summary"""
        st.subheader("🔍 Anomaly Detection Summary")
        
        # Calculate anomaly statistics
        total_anomalies = self._count_anomalies(verification_results)
        
        if total_anomalies == 0:
            st.success("✅ No anomalies detected - Text verification passed!")
            return
        
        # Create anomaly summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Anomalies", 
                total_anomalies,
                delta="Issues Found" if total_anomalies > 0 else None
            )
        
        with col2:
            high_severity = self._count_severity(verification_results, 'high')
            st.metric(
                "High Severity", 
                high_severity,
                delta="Critical" if high_severity > 0 else None,
                delta_color="inverse" if high_severity > 0 else "normal"
            )
        
        with col3:
            medium_severity = self._count_severity(verification_results, 'medium')
            st.metric(
                "Medium Severity", 
                medium_severity,
                delta="Review Needed" if medium_severity > 0 else None,
                delta_color="inverse" if medium_severity > 0 else "normal"
            )
        
        with col4:
            low_severity = self._count_severity(verification_results, 'low')
            st.metric(
                "Low Severity", 
                low_severity,
                delta="Minor Issues" if low_severity > 0 else None
            )
    
    def display_verse_anomalies(self, verse_results: List[Dict]) -> None:
        """Display anomalies for each verse with visual highlighting"""
        st.subheader("📜 Verse-by-Verse Analysis")
        
        for i, verse_result in enumerate(verse_results, 1):
            with st.expander(f"Verse {i} - {self._get_verse_status(verse_result)}", expanded=False):
                self._display_verse_details(verse_result, i)
    
    def display_character_anomalies(self, character_anomalies: List[Dict]) -> None:
        """Display character-level anomalies with highlighting"""
        if not character_anomalies:
            return
        
        st.subheader("🔤 Character-Level Anomalies")
        
        # Create a DataFrame for better visualization
        df = pd.DataFrame(character_anomalies)
        
        # Display in a table with color coding
        st.dataframe(
            df.style.apply(
                lambda row: [f"background-color: {self.anomaly_colors.get(row['severity'], '#FFFFFF')}" 
                           for _ in row], axis=1
            ),
            use_container_width=True
        )
    
    def display_diacritic_anomalies(self, diacritic_anomalies: List[Dict]) -> None:
        """Display diacritic-specific anomalies"""
        if not diacritic_anomalies:
            return
        
        st.subheader("🔤 Diacritic Anomalies")
        
        for anomaly in diacritic_anomalies:
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    st.markdown(f"**Position:** {anomaly.get('position', 'N/A')}")
                
                with col2:
                    st.markdown(f"""
                    **Extracted:** `{anomaly.get('extracted', 'N/A')}`  
                    **Reference:** `{anomaly.get('reference', 'N/A')}`
                    """)
                
                with col3:
                    severity = anomaly.get('severity', 'low')
                    color = self.anomaly_colors.get(severity, '#FFFFFF')
                    st.markdown(f"""
                    <div style="background-color: {color}; padding: 5px; border-radius: 5px; text-align: center;">
                        <strong>{severity.upper()}</strong>
                    </div>
                    """, unsafe_allow_html=True)
    
    def display_semantic_analysis(self, semantic_results: Dict) -> None:
        """Display semantic analysis results"""
        st.subheader("🧠 Semantic Analysis")
        
        # Create metrics for semantic analysis
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Semantic Similarity",
                f"{semantic_results.get('semantic_similarity', 0):.1f}%",
                delta="High" if semantic_results.get('semantic_similarity', 0) > 80 else "Low"
            )
        
        with col2:
            st.metric(
                "Contextual Accuracy",
                f"{semantic_results.get('contextual_accuracy', 0):.1f}%",
                delta="Good" if semantic_results.get('contextual_accuracy', 0) > 70 else "Review"
            )
        
        with col3:
            st.metric(
                "Linguistic Consistency",
                f"{semantic_results.get('linguistic_consistency', 0):.1f}%",
                delta="Consistent" if semantic_results.get('linguistic_consistency', 0) > 80 else "Inconsistent"
            )
        
        # Display confidence score
        confidence = semantic_results.get('confidence_score', 0)
        st.progress(confidence / 100)
        st.caption(f"Overall Confidence: {confidence:.1f}%")
    
    def display_visual_anomalies(self, visual_results: Dict) -> None:
        """Display visual anomalies using charts"""
        st.subheader("👁️ Visual Analysis")
        
        # Create visual analysis charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Layout Compliance', 'Font Consistency', 'Image Quality', 'Margins'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # Layout compliance gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=visual_results.get('layout_compliance', 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Layout Compliance"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "yellow"},
                                {'range': [80, 100], 'color': "green"}]}
            ),
            row=1, col=1
        )
        
        # Font consistency gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=visual_results.get('font_consistency', 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Font Consistency"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkgreen"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "yellow"},
                                {'range': [80, 100], 'color': "green"}]}
            ),
            row=1, col=2
        )
        
        # Image quality gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=visual_results.get('image_quality', 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Image Quality"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkred"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "yellow"},
                                {'range': [80, 100], 'color': "green"}]}
            ),
            row=2, col=1
        )
        
        # Margins gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=visual_results.get('margin_compliance', 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Margin Compliance"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkorange"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "yellow"},
                                {'range': [80, 100], 'color': "green"}]}
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def display_suggestions(self, suggestions: List[str]) -> None:
        """Display improvement suggestions"""
        if not suggestions:
            return
        
        st.subheader("💡 Improvement Suggestions")
        
        for i, suggestion in enumerate(suggestions, 1):
            st.info(f"**{i}.** {suggestion}")
    
    def _count_anomalies(self, verification_results: Dict) -> int:
        """Count total anomalies across all verification methods"""
        total = 0
        
        # Count from different verification methods
        for method in ['text', 'structural', 'semantic', 'visual']:
            if method in verification_results:
                anomalies = verification_results[method].get('anomalies', [])
                total += len(anomalies)
        
        return total
    
    def _count_severity(self, verification_results: Dict, severity: str) -> int:
        """Count anomalies by severity level"""
        count = 0
        
        for method in ['text', 'structural', 'semantic', 'visual']:
            if method in verification_results:
                anomalies = verification_results[method].get('anomalies', [])
                for anomaly in anomalies:
                    if anomaly.get('severity', 'low') == severity:
                        count += 1
        
        return count
    
    def _get_verse_status(self, verse_result: Dict) -> str:
        """Get status emoji for verse"""
        if verse_result.get('score', 0) >= 95:
            return "✅ Excellent"
        elif verse_result.get('score', 0) >= 80:
            return "⚠️ Good"
        elif verse_result.get('score', 0) >= 60:
            return "🔶 Fair"
        else:
            return "❌ Poor"
    
    def _display_verse_details(self, verse_result: Dict, verse_num: int) -> None:
        """Display detailed verse analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Extracted Text:**")
            st.text_area(
                "Extracted",
                verse_result.get('verse', ''),
                height=100,
                key=f"extracted_{verse_num}"
            )
        
        with col2:
            st.markdown("**Reference Text:**")
            st.text_area(
                "Reference",
                verse_result.get('db_verse', ''),
                height=100,
                key=f"reference_{verse_num}"
            )
        
        # Display score and anomalies
        score = verse_result.get('score', 0)
        st.metric("Accuracy Score", f"{score:.1f}%")
        
        if 'anomalies' in verse_result:
            for anomaly in verse_result['anomalies']:
                severity = anomaly.get('severity', 'low')
                color = self.anomaly_colors.get(severity, '#FFFFFF')
                
                st.markdown(f"""
                <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                    <strong>{anomaly.get('type', 'Unknown')}:</strong> {anomaly.get('description', 'No description')}
                </div>
                """, unsafe_allow_html=True)
