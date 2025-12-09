# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary

import omni.ext
import omni.ui as ui
import omni.usd
import carb
from pxr import Usd, UsdGeom, Gf


class PrimPropertyViewerExtension(omni.ext.IExt):
    """Extension hiển thị thuộc tính của prim khi được chọn"""

    def on_startup(self, ext_id):
        """Khởi tạo extension"""
        print("[Prim Property Viewer] Extension startup")

        self._window = ui.Window("Prim Property Viewer", width=400, height=600)
        self._selection_changed_sub = None
        self._current_prim = None
        self._property_frames = {}

        self._build_ui()
        self._setup_selection_listener()

    def _build_ui(self):
        """Xây dựng giao diện"""
        with self._window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(spacing=5, style={"margin": 5}):
                    # Header
                    with ui.HStack(height=30):
                        ui.Label("Selected Prim:", width=100, style={"color": 0xFFCCCCCC})
                        self._prim_path_label = ui.Label("None", style={"color": 0xFFFFAAAA})

                    ui.Separator(height=5)

                    # Tabs cho các loại properties
                    with ui.VStack(spacing=5):
                        # Basic Info Section
                        with ui.CollapsableFrame("Basic Information", height=0):
                            with ui.VStack(spacing=3):
                                self._basic_info_frame = ui.VStack()

                        # Type & Metadata Section
                        with ui.CollapsableFrame("Type & Metadata", height=0):
                            with ui.VStack(spacing=3):
                                self._metadata_frame = ui.VStack()

                        # Transform Section
                        with ui.CollapsableFrame("Transform", height=0):
                            with ui.VStack(spacing=3):
                                self._transform_frame = ui.VStack()

                        # Visibility Section
                        with ui.CollapsableFrame("Visibility", height=0):
                            with ui.VStack(spacing=3):
                                self._visibility_frame = ui.VStack()

                        # Attributes Section
                        with ui.CollapsableFrame("Attributes", height=0, collapsed=False):
                            with ui.ScrollingFrame(height=200):
                                self._attributes_frame = ui.VStack()

                        # Custom Data Section
                        with ui.CollapsableFrame("Custom Data", height=0):
                            with ui.VStack(spacing=3):
                                self._custom_data_frame = ui.VStack()

    def _setup_selection_listener(self):
        """Thiết lập listener để lắng nghe sự kiện selection changed"""
        ctx = omni.usd.get_context()
        events = ctx.get_stage_event_stream()
        self._selection_changed_sub = events.create_subscription_to_pop(
            self._on_stage_event,
            name="Prim Property Viewer Selection Changed"
        )

    def _on_stage_event(self, event):
        """Xử lý sự kiện stage"""
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self._update_selection()

    def _update_selection(self):
        """Cập nhật hiển thị khi selection thay đổi"""
        ctx = omni.usd.get_context()
        selection = ctx.get_selection()
        selected_paths = selection.get_selected_prim_paths()

        if not selected_paths:
            self._prim_path_label.text = "None"
            self._clear_all_frames()
            return

        # Lấy prim đầu tiên được chọn
        prim_path = selected_paths[0]
        self._prim_path_label.text = prim_path

        stage = ctx.get_stage()
        if not stage:
            return

        prim = stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            return

        self._current_prim = prim
        self._display_prim_properties(prim)

    def _clear_all_frames(self):
        """Xóa tất cả nội dung trong các frames"""
        self._basic_info_frame.clear()
        self._metadata_frame.clear()
        self._transform_frame.clear()
        self._visibility_frame.clear()
        self._attributes_frame.clear()
        self._custom_data_frame.clear()

    def _display_prim_properties(self, prim):
        """Hiển thị tất cả properties của prim"""
        self._clear_all_frames()

        # Basic Information
        self._display_basic_info(prim)

        # Type & Metadata
        self._display_metadata(prim)

        # Transform (nếu là Xformable)
        self._display_transform(prim)

        # Visibility
        self._display_visibility(prim)

        # Attributes
        self._display_attributes(prim)

        # Custom Data
        self._display_custom_data(prim)

    def _display_basic_info(self, prim):
        """Hiển thị thông tin cơ bản"""
        with self._basic_info_frame:
            self._add_property_row("Path:", str(prim.GetPath()))
            self._add_property_row("Type:", prim.GetTypeName())
            self._add_property_row("Kind:", Usd.ModelAPI(prim).GetKind())
            self._add_property_row("Active:", str(prim.IsActive()))
            self._add_property_row("Defined:", str(prim.IsDefined()))
            self._add_property_row("Abstract:", str(prim.IsAbstract()))

    def _display_metadata(self, prim):
        """Hiển thị metadata"""
        with self._metadata_frame:
            metadata = prim.GetAllMetadata()
            if metadata:
                for key, value in sorted(metadata.items()):
                    self._add_property_row(f"{key}:", str(value))
            else:
                ui.Label("No metadata", style={"color": 0xFF888888})

    def _display_transform(self, prim):
        """Hiển thị transform nếu prim là Xformable"""
        with self._transform_frame:
            if prim.IsA(UsdGeom.Xformable):
                xformable = UsdGeom.Xformable(prim)

                # Local Transform
                local_xform = xformable.GetLocalTransformation()

                # Extract translation, rotation, scale
                translate = Gf.Vec3d()
                rotation = Gf.Rotation()
                scale = Gf.Vec3d()

                # Decompose matrix
                # Note: This is a simplified extraction
                matrix = local_xform

                # Get translation
                translate = Gf.Vec3d(matrix[3][0], matrix[3][1], matrix[3][2])

                self._add_property_row("Translation:",
                    f"({translate[0]:.3f}, {translate[1]:.3f}, {translate[2]:.3f})")

                # Xform Ops
                xform_ops = xformable.GetOrderedXformOps()
                if xform_ops:
                    ui.Label("Xform Operations:", style={"color": 0xFFCCCCCC})
                    for op in xform_ops:
                        op_name = op.GetOpName()
                        op_value = op.Get()
                        self._add_property_row(f"  {op_name}:", str(op_value))
            else:
                ui.Label("Not an Xformable prim", style={"color": 0xFF888888})

    def _display_visibility(self, prim):
        """Hiển thị visibility"""
        with self._visibility_frame:
            if prim.IsA(UsdGeom.Imageable):
                imageable = UsdGeom.Imageable(prim)

                # Visibility
                visibility_attr = imageable.GetVisibilityAttr()
                if visibility_attr:
                    visibility = visibility_attr.Get()
                    self._add_property_row("Visibility:", str(visibility))

                # Purpose
                purpose_attr = imageable.GetPurposeAttr()
                if purpose_attr:
                    purpose = purpose_attr.Get()
                    self._add_property_row("Purpose:", str(purpose))
            else:
                ui.Label("Not an Imageable prim", style={"color": 0xFF888888})

    def _display_attributes(self, prim):
        """Hiển thị tất cả attributes"""
        with self._attributes_frame:
            attributes = prim.GetAttributes()

            if not attributes:
                ui.Label("No attributes", style={"color": 0xFF888888})
                return

            ui.Label(f"Total Attributes: {len(attributes)}",
                    style={"color": 0xFFCCCCCC, "font_size": 14})

            for attr in attributes:
                attr_name = attr.GetName()
                attr_type = attr.GetTypeName()
                attr_value = attr.Get()

                # Hiển thị attribute
                with ui.HStack(height=25):
                    with ui.VStack(width=150):
                        ui.Label(attr_name, style={"color": 0xFFAAAAFF})
                        ui.Label(f"({attr_type})", style={"color": 0xFF888888, "font_size": 10})

                    ui.Spacer(width=10)

                    # Hiển thị giá trị
                    value_str = self._format_value(attr_value)
                    ui.Label(value_str, style={"color": 0xFFCCFFCC}, word_wrap=True)

                ui.Separator(height=1)

    def _display_custom_data(self, prim):
        """Hiển thị custom data"""
        with self._custom_data_frame:
            custom_data = prim.GetCustomData()

            if custom_data:
                for key, value in sorted(custom_data.items()):
                    self._add_property_row(f"{key}:", str(value))
            else:
                ui.Label("No custom data", style={"color": 0xFF888888})

    def _add_property_row(self, label, value):
        """Thêm một row hiển thị property"""
        with ui.HStack(height=20):
            ui.Label(label, width=120, style={"color": 0xFFAAAAFF})
            ui.Label(str(value), style={"color": 0xFFCCFFCC}, word_wrap=True)

    def _format_value(self, value):
        """Format giá trị để hiển thị"""
        if value is None:
            return "None"

        # Vector types
        if isinstance(value, (Gf.Vec2d, Gf.Vec2f, Gf.Vec2h, Gf.Vec2i)):
            return f"({value[0]:.3f}, {value[1]:.3f})"

        if isinstance(value, (Gf.Vec3d, Gf.Vec3f, Gf.Vec3h, Gf.Vec3i)):
            return f"({value[0]:.3f}, {value[1]:.3f}, {value[2]:.3f})"

        if isinstance(value, (Gf.Vec4d, Gf.Vec4f, Gf.Vec4h, Gf.Vec4i)):
            return f"({value[0]:.3f}, {value[1]:.3f}, {value[2]:.3f}, {value[3]:.3f})"

        # Matrix types
        if isinstance(value, (Gf.Matrix4d, Gf.Matrix3d, Gf.Matrix2d)):
            return f"Matrix {value.dimension}x{value.dimension}"

        # Float types
        if isinstance(value, (float, Gf.Half)):
            return f"{float(value):.6f}"

        # List/Array types
        if isinstance(value, (list, tuple)):
            if len(value) > 5:
                return f"[{len(value)} items]"
            return str(value)

        return str(value)

    def on_shutdown(self):
        """Cleanup khi extension bị disable"""
        print("[Prim Property Viewer] Extension shutdown")

        # Cleanup subscription
        if self._selection_changed_sub:
            self._selection_changed_sub.unsubscribe()
            self._selection_changed_sub = None

        # Cleanup window
        if self._window:
            self._window.destroy()
            self._window = None