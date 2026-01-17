try:
    from PySide6 import QtWidgets, QtCore
except Exception:
    from PySide2 import QtWidgets, QtCore

from .analysis import analyze_model
import os

class AnalyzeDialog(QtWidgets.QDialog):
    def __init__(self, file_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asset Analysis")
        self.resize(720, 480)

        layout = QtWidgets.QVBoxLayout(self)

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        btns.rejected.connect(self.close)
        layout.addWidget(btns)

        self.run_analysis(file_paths)

    def run_analysis(self, paths):
        output = []

        total = len(paths)
        if total == 0:
            return

        progress = QtWidgets.QProgressDialog(
            "Analyzing assets...",
            "Cancel",
            0,
            total,
            self
        )
        progress.setWindowTitle("Analysis")
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)  # show immediately
        progress.setValue(0)

        for i, path in enumerate(paths):
            QtWidgets.QApplication.processEvents()

            if progress.wasCanceled():
                output.append("Analysis canceled by user.")
                break

            progress.setValue(i)

            if not os.path.isfile(path):
                continue

            report = analyze_model(path)

            output.append("Model: {}".format(path))

            for m in report["meshes"]:
                output.append(
                    "  Mesh: {}\n"
                    "    Verts: {} | "
                    "Polys: {} | "
                    "Ngons: {} | "
                    "UV sets: {}".format(
                        m["mesh"],
                        m["vertices"],
                        m["polygons"],
                        m["ngons"],
                        m["uv_sets"]
                    )
                )

            for err in report["errors"]:
                output.append("  ERROR: {}".format(err))

            output.append("")

        progress.setValue(total)
        progress.close()

        self.text.setPlainText("\n".join(output))


def show_analyze_panel(file_paths, parent=None):
    dlg = AnalyzeDialog(file_paths, parent)
    dlg.exec()
