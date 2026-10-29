class MaterialTheme:
    """
    Material Design 3 (Material You) Design Tokens & QSS Stylesheet.
    """
    # Palette
    COLOR_PRIMARY = "#006399"
    COLOR_PRIMARY_HOVER = "#005584"
    COLOR_PRIMARY_PRESSED = "#004770"
    COLOR_PRIMARY_CONTAINER = "#CCE5FF"
    COLOR_ON_PRIMARY = "#FFFFFF"

    COLOR_SURFACE = "#F8FAFC"
    COLOR_SURFACE_CARD = "#FFFFFF"
    COLOR_SURFACE_HOVER = "#F1F5F9"
    COLOR_SURFACE_VARIANT = "#E2E8F0"

    COLOR_TEXT_PRIMARY = "#0F172A"
    COLOR_TEXT_SECONDARY = "#64748B"
    COLOR_TEXT_TERTIARY = "#94A3B8"

    COLOR_OUTLINE = "#CBD5E1"
    COLOR_OUTLINE_LIGHT = "#E2E8F0"
    COLOR_OUTLINE_ACTIVE = "#38BDF8"

    COLOR_SUCCESS = "#10B981"
    COLOR_SUCCESS_BG = "#ECFDF5"
    COLOR_ERROR = "#EF4444"
    COLOR_ERROR_BG = "#FEF2F2"

    FONT_FAMILY = "Segoe UI, 'Microsoft YaHei', sans-serif"

    @classmethod
    def get_application_qss(cls) -> str:
        return f"""
        QWidget {{
            font-family: {cls.FONT_FAMILY};
            color: {cls.COLOR_TEXT_PRIMARY};
            font-size: 13px;
        }}

        QMainWindow, QDialog {{
            background-color: {cls.COLOR_SURFACE};
        }}

        /* App Header */
        #HeaderFrame {{
            background-color: {cls.COLOR_SURFACE_CARD};
            border-bottom: 1px solid {cls.COLOR_OUTLINE_LIGHT};
            padding: 8px 16px;
        }}

        #AppTitle {{
            font-size: 18px;
            font-weight: 700;
            color: {cls.COLOR_PRIMARY};
        }}

        #AppSubtitle {{
            font-size: 12px;
            color: {cls.COLOR_TEXT_SECONDARY};
        }}

        #StatusPill {{
            background-color: #ECFDF5;
            color: #065F46;
            font-size: 11px;
            font-weight: 600;
            border-radius: 10px;
            padding: 3px 10px;
            border: 1px solid #A7F3D0;
        }}

        /* Hero Drop Zone */
        #DropZoneFrame {{
            background-color: {cls.COLOR_SURFACE_CARD};
            border: 2px dashed #93C5FD;
            border-radius: 16px;
            padding: 24px;
        }}

        #DropZoneFrame[dragOver="true"] {{
            background-color: #EFF6FF;
            border: 2px solid #2563EB;
        }}

        #DropZoneTitle {{
            font-size: 16px;
            font-weight: 600;
            color: {cls.COLOR_TEXT_PRIMARY};
            margin-top: 8px;
        }}

        #DropZoneDesc {{
            font-size: 12px;
            color: {cls.COLOR_TEXT_SECONDARY};
            margin-top: 4px;
        }}

        /* Filled Primary Button */
        QPushButton.primary-btn {{
            background-color: {cls.COLOR_PRIMARY};
            color: {cls.COLOR_ON_PRIMARY};
            font-weight: 600;
            border: none;
            border-radius: 10px;
            padding: 8px 18px;
            min-height: 20px;
        }}

        QPushButton.primary-btn:hover {{
            background-color: {cls.COLOR_PRIMARY_HOVER};
        }}

        QPushButton.primary-btn:pressed {{
            background-color: {cls.COLOR_PRIMARY_PRESSED};
        }}

        /* Tonal/Outlined Button */
        QPushButton.tonal-btn {{
            background-color: {cls.COLOR_PRIMARY_CONTAINER};
            color: #002D4C;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            padding: 8px 16px;
        }}

        QPushButton.tonal-btn:hover {{
            background-color: #B8DBFF;
        }}

        /* Outlined Button */
        QPushButton.outlined-btn {{
            background-color: {cls.COLOR_SURFACE_CARD};
            color: {cls.COLOR_TEXT_PRIMARY};
            border: 1px solid {cls.COLOR_OUTLINE};
            border-radius: 8px;
            padding: 6px 12px;
            font-weight: 500;
        }}

        QPushButton.outlined-btn:hover {{
            background-color: {cls.COLOR_SURFACE_HOVER};
            border-color: #94A3B8;
        }}

        /* Action/Icon Button */
        QPushButton.icon-btn {{
            background-color: transparent;
            border: 1px solid {cls.COLOR_OUTLINE_LIGHT};
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
            color: {cls.COLOR_TEXT_SECONDARY};
        }}

        QPushButton.icon-btn:hover {{
            background-color: #F1F5F9;
            color: {cls.COLOR_PRIMARY};
            border-color: #93C5FD;
        }}

        /* Preset ComboBox */
        QComboBox {{
            background-color: {cls.COLOR_SURFACE_CARD};
            border: 1px solid {cls.COLOR_OUTLINE};
            border-radius: 8px;
            padding: 5px 12px;
            font-weight: 500;
            min-width: 130px;
        }}

        QComboBox:hover {{
            border-color: #94A3B8;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {cls.COLOR_SURFACE_CARD};
            border: 1px solid {cls.COLOR_OUTLINE_LIGHT};
            border-radius: 8px;
            selection-background-color: {cls.COLOR_PRIMARY_CONTAINER};
            selection-color: #002D4C;
            padding: 4px;
        }}

        /* History Card Area */
        #HistoryContainer {{
            background-color: {cls.COLOR_SURFACE_CARD};
            border: 1px solid {cls.COLOR_OUTLINE_LIGHT};
            border-radius: 14px;
            padding: 12px;
        }}

        #HistoryHeaderLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {cls.COLOR_TEXT_PRIMARY};
        }}

        QScrollArea {{
            border: none;
            background-color: transparent;
        }}

        /* Task Item Card */
        QFrame.task-item-card {{
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 10px 14px;
        }}

        QFrame.task-item-card:hover {{
            background-color: #F1F5F9;
            border-color: #CBD5E1;
        }}

        QLabel.task-filename {{
            font-weight: 600;
            font-size: 13px;
            color: {cls.COLOR_TEXT_PRIMARY};
        }}

        QLabel.task-path {{
            font-size: 11px;
            color: {cls.COLOR_TEXT_SECONDARY};
        }}

        QLabel.task-badge-success {{
            background-color: {cls.COLOR_SUCCESS_BG};
            color: {cls.COLOR_SUCCESS};
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            padding: 2px 8px;
            border: 1px solid #A7F3D0;
        }}

        QLabel.task-badge-error {{
            background-color: {cls.COLOR_ERROR_BG};
            color: {cls.COLOR_ERROR};
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            padding: 2px 8px;
            border: 1px solid #FECACA;
        }}

        /* QScrollBar */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: #CBD5E1;
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #94A3B8;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* CheckBox */
        QCheckBox {{
            font-size: 12px;
            color: {cls.COLOR_TEXT_SECONDARY};
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid {cls.COLOR_OUTLINE};
            background-color: #FFFFFF;
        }}
        QCheckBox::indicator:checked {{
            background-color: {cls.COLOR_PRIMARY};
            border-color: {cls.COLOR_PRIMARY};
            image: none;
        }}
        """
