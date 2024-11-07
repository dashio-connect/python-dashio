"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import annotations
import logging
from ..constants import BAD_CHARS
from .control import Control, ControlPosition, ControlConfig, _get_title_position, _get_precision
from .enums import (
    Precision,
    TitlePosition
)


logger = logging.getLogger(__name__)


class TableConfig(ControlConfig):
    """TableConfig"""

    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        precision: Precision,
        font_size: int,
        label_width_percent: int,
        columns: int,
        column_headings: list[str],
        control_position: ControlPosition | None
    ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        ch = [heading.translate(BAD_CHARS) for heading in column_headings]
        self.cfg["fontSize"] = font_size
        self.cfg["labelWidthPcnt"] = label_width_percent
        self.cfg["columns"] = columns
        self.cfg["colHeadings"] = ch
        self.cfg["precision"] = precision.value

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates TableConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        TableConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_precision(cfg_dict["precision"]),
            cfg_dict["fontSize"],
            cfg_dict["labelWidthPcnt"],
            cfg_dict["columns"],
            cfg_dict["colHeadings"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls


class TableRow:
    """A Table Row
    """
    def __init__(
            self,
            label: str | None = None,
            columns: list[str] | None = None,
            units: str | None = None,
            ) -> None:
        self.label = label
        if columns is None:
            self.columns = columns
        else:
            self.columns = [column.translate(BAD_CHARS) for column in columns]
        self.units = units


class Table(Control):
    """A Table control
    """

    def __init__(
        self,
        control_id: str,
        title="A Table Box",
        title_position=TitlePosition.BOTTOM,
        precision=Precision.OFF,
        font_size: int = 12,
        label_width_percent: int = 50,
        columns: int = 2,
        column_headings: list[str] = None,
        control_position=None,
        column_no=1
    ):
        """Table control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default None
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the **Dash** app, by default None
        precision : Precision, optional
            precision, by default Precision.OFF
        font_size : int, by default 12
            The size of the font.
        label_width_percent : int
            Label width as a percent.
        columns : int
            Number of table columns including the label.
        column_headings : List
            The headings for the table columns.
        column_no : int, optional default is 1. Must be 1..3
            The Dash App reports its screen size in columns. column_no allows you to specify which column no to load into.
            Each control can store three configs that define how the device looks for Dash apps installed on single column
            phones or 2 column fold out phones or 3 column tablets.
        """
        super().__init__("TBL", control_id)
        ch = column_headings
        if column_headings is not None:
            ch = [heading.translate(BAD_CHARS) for heading in column_headings]
        self._app_columns_cfg[str(column_no)].append(
            TableConfig(
                control_id,
                title,
                title_position,
                precision,
                font_size,
                label_width_percent,
                columns,
                ch,
                control_position
            )
        )
        self._rows = []
        self._max_columns = columns

    def get_state(self):
        return "".join([self._send_row(index, row) for index, row in enumerate(self._rows)])

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict, column_no=1):
        """Instantiates Table from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Table
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_precision(cfg_dict["precision"]),
            cfg_dict["fontSize"],
            cfg_dict["labelWidthPcnt"],
            cfg_dict["columns"],
            cfg_dict["colHeadings"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
            column_no
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def _send_row(self, row_number: int, table_row: TableRow | None) -> str:
        header_str = self._control_hdr_str
        if table_row is None:
            return f"{header_str}{row_number}\n"
        columns = '\t'.join(map(str, table_row.columns[:self._max_columns - 1]))
        if table_row.units is not None:
            row_label = table_row.label
            if table_row.label is None:
                row_label = ""
            return f"{header_str}{row_number}\t{columns}\t{row_label}\t{table_row.units}\n"
        else:
            if table_row.label is None:
                return f"{header_str}{row_number}\t{columns}\n"
            return f"{header_str}{row_number}\t{columns}\t{row_label}\n"

    def add_table_row(self, table_row: TableRow):
        """Add a row to the table and send it"""
        self._rows.append(table_row)
        self.state_str = self._send_row(len(self._rows) - 1, table_row)

    def update_table_row(self, table_row: TableRow, row_number: int) -> int:
        """Update the row at row_number. If it doesn't exist then append it.

        Parameters
        ----------
        table_row : TableRow
            The updated row
        row_number : int
            The row index to update

        Returns
        -------
        int
            The index of the updated row.
        """
        if row_number < len(self._rows):
            self._rows[row_number] = table_row
            self.state_str = self._send_row(row_number, table_row)
            return row_number
        self._rows.append(table_row)
        self.state_str = self._send_row(len(self._rows) - 1, table_row)
        return len(self._rows)-1

    def clear_row(self, row_number: int):
        """Clears the row at row_number

        Parameters
        ----------
        row_number : int
            The row to clear
        """
        if 0 <= row_number < len(self._rows):
            self._rows[row_number] = None
            header_str = self._control_hdr_str + f"{row_number}\n"
            self.state_str = header_str

    def clear_table(self):
        """Clears the table
        """
        self._rows = []
        header_str = self._control_hdr_str + '\n'
        self.state_str = header_str
