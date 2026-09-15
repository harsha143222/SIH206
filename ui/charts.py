"""
EduMind AI - Reusable Plotly & Streamlit Visualization Charts
Renders modern, dark/light theme aware responsive charts for Student & Admin analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any


def render_subject_performance_chart(subject_data: List[Dict[str, Any]]):
    """Render horizontal bar chart for subject performance percentages."""
    if not subject_data:
        st.info("📊 No subject data available yet. Start studying or take a quiz!")
        return

    df = pd.DataFrame(subject_data)
    fig = px.bar(
        df,
        x="progress_percentage",
        y="subject",
        orientation="h",
        text="progress_percentage",
        color="progress_percentage",
        color_continuous_scale=["#EF4444", "#F59E0B", "#10B981", "#3B82F6"],
        range_color=[0, 100],
        title="Subject Performance (%)",
        labels={"progress_percentage": "Score / Progress (%)", "subject": "Subject"}
    )
    fig.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside',
        marker_line_color='rgba(255, 255, 255, 0.2)',
        marker_line_width=1
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC", family="sans-serif"),
        coloraxis_showscale=False,
        height=320,
        margin=dict(l=20, r=40, t=40, b=20),
        xaxis=dict(range=[0, 105], gridcolor="rgba(148, 163, 184, 0.1)"),
        yaxis=dict(gridcolor="rgba(148, 163, 184, 0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)


def render_topic_performance_chart(topic_data: List[Dict[str, Any]]):
    """Render vertical bar chart for topic level mastery scores."""
    if not topic_data:
        st.info("📊 No topic performance data available yet.")
        return

    df = pd.DataFrame(topic_data)
    fig = px.bar(
        df,
        x="topic",
        y="average_score",
        color="mastery_level",
        color_discrete_map={
            "Strong": "#10B981",
            "Needs Practice": "#F59E0B",
            "Needs Revision": "#EF4444",
            "Not Tested": "#94A3B8"
        },
        text="average_score",
        title="Topic Mastery Scores (%)",
        labels={"average_score": "Average Score (%)", "topic": "Topic"}
    )
    fig.update_traces(
        texttemplate='%{text:.0f}%',
        textposition='outside'
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC", family="sans-serif"),
        height=340,
        margin=dict(l=20, r=20, t=40, b=40),
        yaxis=dict(range=[0, 110], gridcolor="rgba(148, 163, 184, 0.1)"),
        xaxis=dict(gridcolor="rgba(148, 163, 184, 0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)


def render_quiz_score_trend_chart(trend_data: Dict[str, Any]):
    """Render interactive line chart for quiz score trend over time."""
    if not trend_data.get("has_data"):
        st.info("📈 Not enough quiz data yet to display trend lines. Complete your first quiz to see your progress!")
        return

    timeline = trend_data.get("timeline", [])
    df = pd.DataFrame(timeline)
    
    # Filter out empty scores
    df_scores = df.dropna(subset=["average_quiz_score"])
    if df_scores.empty:
        st.info("📈 Not enough historical quiz attempts yet to plot trend lines.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_scores["display_date"],
        y=df_scores["average_quiz_score"],
        mode='lines+markers',
        name='Avg Quiz Score (%)',
        line=dict(color='#60A5FA', width=3),
        marker=dict(size=8, color='#A855F7', symbol='circle'),
        fill='tozeroy',
        fillcolor='rgba(96, 165, 250, 0.15)'
    ))
    fig.update_layout(
        title=f"Quiz Score Trend (Past {trend_data.get('days', 30)} Days)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC", family="sans-serif"),
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        yaxis=dict(range=[0, 105], title="Score (%)", gridcolor="rgba(148, 163, 184, 0.1)"),
        xaxis=dict(title="Date", gridcolor="rgba(148, 163, 184, 0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)


def render_study_activity_chart(trend_data: Dict[str, Any]):
    """Render combo bar/line chart for daily study time & questions asked."""
    if not trend_data.get("has_data"):
        st.info("📊 No daily study activity recorded yet.")
        return

    timeline = trend_data.get("timeline", [])
    df = pd.DataFrame(timeline)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["display_date"],
        y=df["questions_asked"],
        name="AI Questions Asked",
        marker_color="#818CF8"
    ))
    fig.add_trace(go.Bar(
        x=df["display_date"],
        y=df["quiz_attempts"],
        name="Quiz Attempts",
        marker_color="#34D399"
    ))
    fig.update_layout(
        title=f"Learning Activity Breakdown (Past {trend_data.get('days', 30)} Days)",
        barmode='stack',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC", family="sans-serif"),
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        yaxis=dict(title="Count", gridcolor="rgba(148, 163, 184, 0.1)"),
        xaxis=dict(title="Date", gridcolor="rgba(148, 163, 184, 0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)


def render_difficulty_performance_chart(diff_data: Dict[str, Any]):
    """Render bar chart for performance by question difficulty."""
    if not diff_data:
        st.info("🎯 Take a quiz to see difficulty-specific performance stats.")
        return

    items = []
    for diff, stats in diff_data.items():
        items.append({
            "difficulty": diff,
            "avg_score": stats.get("avg_score", 0.0),
            "count": stats.get("count", 0)
        })

    df = pd.DataFrame(items)
    fig = px.bar(
        df,
        x="difficulty",
        y="avg_score",
        color="difficulty",
        color_discrete_map={
            "Easy": "#10B981",
            "Medium": "#F59E0B",
            "Hard": "#EF4444"
        },
        text="avg_score",
        title="Performance by Difficulty Level",
        labels={"avg_score": "Average Score (%)", "difficulty": "Difficulty"}
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC", family="sans-serif"),
        height=300,
        margin=dict(l=20, r=20, t=40, b=30),
        yaxis=dict(range=[0, 110], gridcolor="rgba(148, 163, 184, 0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)
