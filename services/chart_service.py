import plotly.express as px
import pandas as pd
import os

class ChartService:
    @staticmethod
    def render_chart(chart_type: str, columns: list, rows: list, x: str, y: str = None, title: str = None, output_path: str = "exports/chart.png") -> dict:
        """
        Génère un graphique via Plotly et l'exporte en PNG via kaleido.
        """
        try:
            df = pd.DataFrame(rows, columns=columns)
            
            if chart_type == 'bar':
                fig = px.bar(df, x=x, y=y, title=title)
            elif chart_type == 'line':
                fig = px.line(df, x=x, y=y, title=title)
            elif chart_type == 'pie':
                fig = px.pie(df, names=x, values=y, title=title)
            elif chart_type == 'donut':
                fig = px.pie(df, names=x, values=y, title=title, hole=0.4)
            elif chart_type == 'scatter':
                fig = px.scatter(df, x=x, y=y, title=title)
            elif chart_type == 'histogram':
                fig = px.histogram(df, x=x, title=title)
            elif chart_type == 'box':
                fig = px.box(df, y=y, x=x, title=title)
            elif chart_type == 'area':
                fig = px.area(df, x=x, y=y, title=title)
            else:
                return {'ok': False, 'erreur': f"Type de graphique {chart_type} non supporté."}
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Necessite le package 'kaleido' pour l'export statique
            fig.write_image(output_path)
            
            return {'ok': True, 'filepath': output_path}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}
