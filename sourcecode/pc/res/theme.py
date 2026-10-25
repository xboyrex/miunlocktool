import customtkinter as ctk


class MaterialColors:
    LIGHT_SCHEME = {
        "primary": "#E50914",
        "on_primary": "#FFFFFF",
        "primary_container": "#93000A",
        "on_primary_container": "#FFDAD6",
        "secondary": "#1E293B",
        "on_secondary": "#FFFFFF",
        "secondary_container": "#E2E8F0",
        "on_secondary_container": "#0F172A",
        "tertiary": "#E50914",
        "on_tertiary": "#FFFFFF",
        "tertiary_container": "#FFDAD6",
        "on_tertiary_container": "#410002",
        "surface": "#0E1118",
        "on_surface": "#F8FAFC",
        "surface_variant": "#191F2E",
        "on_surface_variant": "#CBD5E1",
        "background": "#090B10",
        "on_background": "#F8FAFC",
        "error": "#EF4444",
        "on_error": "#FFFFFF",
        "error_container": "#7F1D1D",
        "on_error_container": "#FEE2E2",
        "outline": "#E50914",
        "outline_variant": "#262C3A",
        "shadow": "#000000",
        "scrim": "#000000",
        "inverse_surface": "#F8FAFC",
        "inverse_on_surface": "#090B10",
        "inverse_primary": "#E50914",
        "surface_tint": "#E50914",
        "primary_fixed": "#FFDAD6",
        "on_primary_fixed": "#410002",
        "primary_fixed_dim": "#FFB4AB",
        "on_primary_fixed_variant": "#93000A",
        "secondary_fixed": "#E2E8F0",
        "on_secondary_fixed": "#0F172A",
        "secondary_fixed_dim": "#CBD5E1",
        "on_secondary_fixed_variant": "#334155",
        "tertiary_fixed": "#FFDAD6",
        "on_tertiary_fixed": "#410002",
        "tertiary_fixed_dim": "#FFB4AB",
        "on_tertiary_fixed_variant": "#93000A",
        "surface_dim": "#06070A",
        "surface_bright": "#1E2433",
        "surface_container_lowest": "#050608",
        "surface_container_low": "#0B0E14",
        "surface_container": "#10141D",
        "surface_container_high": "#161B28",
        "surface_container_highest": "#1F2637",
    }

    DARK_SCHEME = {
        "primary": "#E50914",
        "on_primary": "#FFFFFF",
        "primary_container": "#93000A",
        "on_primary_container": "#FFDAD6",
        "secondary": "#94A3B8",
        "on_secondary": "#0F172A",
        "secondary_container": "#1E293B",
        "on_secondary_container": "#F8FAFC",
        "tertiary": "#FF333D",
        "on_tertiary": "#FFFFFF",
        "tertiary_container": "#7F1D1D",
        "on_tertiary_container": "#FECACA",
        "surface": "#0E1118",
        "on_surface": "#F8FAFC",
        "surface_variant": "#191F2E",
        "on_surface_variant": "#94A3B8",
        "background": "#080A0F",
        "on_background": "#F8FAFC",
        "error": "#F87171",
        "on_error": "#450A0A",
        "error_container": "#7F1D1D",
        "on_error_container": "#FEE2E2",
        "outline": "#E50914",
        "outline_variant": "#252B3B",
        "shadow": "#000000",
        "scrim": "#000000",
        "inverse_surface": "#F8FAFC",
        "inverse_on_surface": "#080A0F",
        "inverse_primary": "#E50914",
        "surface_tint": "#E50914",
        "primary_fixed": "#FFDAD6",
        "on_primary_fixed": "#410002",
        "primary_fixed_dim": "#FFB4AB",
        "on_primary_fixed_variant": "#93000A",
        "secondary_fixed": "#E2E8F0",
        "on_secondary_fixed": "#0F172A",
        "secondary_fixed_dim": "#CBD5E1",
        "on_secondary_fixed_variant": "#334155",
        "tertiary_fixed": "#FFDAD6",
        "on_tertiary_fixed": "#410002",
        "tertiary_fixed_dim": "#FFB4AB",
        "on_tertiary_fixed_variant": "#93000A",
        "surface_dim": "#050608",
        "surface_bright": "#1E2433",
        "surface_container_lowest": "#050608",
        "surface_container_low": "#0B0E14",
        "surface_container": "#10141D",
        "surface_container_high": "#161B28",
        "surface_container_highest": "#1F2637",
    }

    @classmethod
    def get_color(cls, color_name, dark_mode=True):
        scheme = cls.DARK_SCHEME if dark_mode else cls.LIGHT_SCHEME
        return scheme.get(color_name, "#000000")

    @classmethod
    def set_accent_color(cls, primary_color, on_primary="#1C1B1F", container=None, secondary=None):
        cls.DARK_SCHEME["primary"] = primary_color
        cls.DARK_SCHEME["on_primary"] = on_primary
        if container:
            cls.DARK_SCHEME["primary_container"] = container
        if secondary:
            cls.DARK_SCHEME["secondary"] = secondary
        cls.DARK_SCHEME["surface_tint"] = primary_color
        cls.DARK_SCHEME["inverse_primary"] = primary_color


class MaterialTypography:
    DISPLAY_LARGE = ("Segoe UI", 57, "normal")
    DISPLAY_MEDIUM = ("Segoe UI", 45, "normal")
    DISPLAY_SMALL = ("Segoe UI", 36, "normal")

    HEADLINE_LARGE = ("Segoe UI", 32, "normal")
    HEADLINE_MEDIUM = ("Segoe UI", 28, "normal")
    HEADLINE_SMALL = ("Segoe UI", 24, "normal")

    TITLE_LARGE = ("Segoe UI", 22, "bold")
    TITLE_MEDIUM = ("Segoe UI", 16, "bold")
    TITLE_SMALL = ("Segoe UI", 14, "bold")

    LABEL_LARGE = ("Segoe UI", 14, "bold")
    LABEL_MEDIUM = ("Segoe UI", 12, "bold")
    LABEL_SMALL = ("Segoe UI", 11, "bold")

    BODY_LARGE = ("Segoe UI", 16, "normal")
    BODY_MEDIUM = ("Segoe UI", 14, "normal")
    BODY_SMALL = ("Segoe UI", 12, "normal")


class MD3Button(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        button_type = kwargs.pop('button_type', 'filled')
        size = kwargs.pop('size', 'medium')

        dark_mode = ctk.get_appearance_mode() == "Dark"

        base_kwargs = {
            'corner_radius': 20 if size == 'medium' else (16 if size == 'small' else 24),
            'border_width': 0,
            'font': MaterialTypography.LABEL_LARGE,
        }

        if button_type == 'filled':
            base_kwargs.update({
                'fg_color': MaterialColors.get_color('primary', dark_mode),
                'hover_color': MaterialColors.get_color('primary_container', dark_mode),
                'text_color': MaterialColors.get_color('on_primary', dark_mode),
            })
        elif button_type == 'outlined':
            base_kwargs.update({
                'fg_color': 'transparent',
                'border_width': 1,
                'border_color': MaterialColors.get_color('outline', dark_mode),
                'text_color': MaterialColors.get_color('primary', dark_mode),
                'hover_color': MaterialColors.get_color('surface_container', dark_mode),
            })
        elif button_type == 'text':
            base_kwargs.update({
                'fg_color': 'transparent',
                'text_color': MaterialColors.get_color('primary', dark_mode),
                'hover_color': MaterialColors.get_color('surface_container', dark_mode),
            })
        elif button_type == 'elevated':
            base_kwargs.update({
                'fg_color': MaterialColors.get_color('surface_container_low', dark_mode),
                'border_width': 0,
                'text_color': MaterialColors.get_color('primary', dark_mode),
                'hover_color': MaterialColors.get_color('surface_container', dark_mode),
            })

        if size == 'small':
            base_kwargs['height'] = 32
        elif size == 'medium':
            base_kwargs['height'] = 40
        elif size == 'large':
            base_kwargs['height'] = 56

        base_kwargs.update(kwargs)
        super().__init__(master, **base_kwargs)


class MD3Entry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        dark_mode = ctk.get_appearance_mode() == "Dark"
        base_kwargs = {
            'corner_radius': 4,
            'border_width': 2,
            'font': MaterialTypography.BODY_MEDIUM,
            'height': 40,
            'fg_color': MaterialColors.get_color('surface_container_lowest', dark_mode),
            'border_color': MaterialColors.get_color('outline', dark_mode),
            'text_color': MaterialColors.get_color('on_surface', dark_mode),
        }
        base_kwargs.update(kwargs)
        super().__init__(master, **base_kwargs)


class MD3Label(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        typography = kwargs.pop('typography', 'body_medium')
        font_map = {
            'display_large': MaterialTypography.DISPLAY_LARGE,
            'display_medium': MaterialTypography.DISPLAY_MEDIUM,
            'display_small': MaterialTypography.DISPLAY_SMALL,
            'headline_large': MaterialTypography.HEADLINE_LARGE,
            'headline_medium': MaterialTypography.HEADLINE_MEDIUM,
            'headline_small': MaterialTypography.HEADLINE_SMALL,
            'title_large': MaterialTypography.TITLE_LARGE,
            'title_medium': MaterialTypography.TITLE_MEDIUM,
            'title_small': MaterialTypography.TITLE_SMALL,
            'label_large': MaterialTypography.LABEL_LARGE,
            'label_medium': MaterialTypography.LABEL_MEDIUM,
            'label_small': MaterialTypography.LABEL_SMALL,
            'body_large': MaterialTypography.BODY_LARGE,
            'body_medium': MaterialTypography.BODY_MEDIUM,
            'body_small': MaterialTypography.BODY_SMALL,
        }

        dark_mode = ctk.get_appearance_mode() == "Dark"
        base_kwargs = {
            'font': font_map.get(typography, MaterialTypography.BODY_MEDIUM),
            'text_color': MaterialColors.get_color('on_surface', dark_mode),
        }
        base_kwargs.update(kwargs)
        super().__init__(master, **base_kwargs)


class MD3Card(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        elevation = kwargs.pop('elevation', 1)
        dark_mode = ctk.get_appearance_mode() == "Dark"

        if elevation == 0:
            border_width = 1
            border_color = MaterialColors.get_color('outline_variant', dark_mode)
        else:
            border_width = 0
            border_color = None

        base_kwargs = {
            'corner_radius': 12,
            'border_width': border_width,
            'border_color': border_color,
            'fg_color': MaterialColors.get_color('surface_container', dark_mode),
        }
        base_kwargs.update(kwargs)
        super().__init__(master, **base_kwargs)


class MD3Switch(ctk.CTkSwitch):
    def __init__(self, master, **kwargs):
        dark_mode = ctk.get_appearance_mode() == "Dark"
        base_kwargs = {
            'font': MaterialTypography.LABEL_MEDIUM,
            'fg_color': MaterialColors.get_color('surface_container_high', dark_mode),
            'progress_color': MaterialColors.get_color('primary', dark_mode),
            'button_color': MaterialColors.get_color('on_primary', dark_mode),
            'button_hover_color': MaterialColors.get_color('primary_container', dark_mode),
            'text_color': MaterialColors.get_color('on_surface', dark_mode),
        }
        base_kwargs.update(kwargs)
        super().__init__(master, **base_kwargs)


class MD3SegmentedButton(ctk.CTkSegmentedButton):
    def __init__(self, master, **kwargs):
        dark_mode = ctk.get_appearance_mode() == "Dark"
        base_kwargs = {
            'height': 40,
            'corner_radius': 20,
            'border_width': 1,
            'font': MaterialTypography.LABEL_MEDIUM,
            'fg_color': MaterialColors.get_color('surface_container', dark_mode),
            'selected_color': MaterialColors.get_color('primary', dark_mode),
            'selected_hover_color': MaterialColors.get_color('primary_container', dark_mode),
            'unselected_color': MaterialColors.get_color('surface_container_low', dark_mode),
            'unselected_hover_color': MaterialColors.get_color('surface_container', dark_mode),
            'text_color': MaterialColors.get_color('on_surface', dark_mode),
            'text_color_disabled': MaterialColors.get_color('on_surface_variant', dark_mode),
        }
        base_kwargs.update(kwargs)
        super().__init__(master, **base_kwargs)