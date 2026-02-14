try:
    from PySide6 import QtWidgets, QtCore
except Exception:
    from PySide2 import QtWidgets, QtCore

from .analysis import analyze_model
import os

class AnalyzeDialog(QtWidgets.QDialog):
    """
    Dialog that runs asset analysis on a list of file paths
    and displays the results in a read-only text view.
    """

    def __init__(self, file_paths, parent=None):
        super().__init__(parent)

        # Window setup
        self.setWindowTitle("Asset Analysis")
        self.resize(720, 480)

        layout = QtWidgets.QVBoxLayout(self)

        # Read-only output area for analysis results
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

        # Close button
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        btns.rejected.connect(self.close)
        layout.addWidget(btns)

        # Start analysis immediately after dialog creation
        self.run_analysis(file_paths)

    def run_analysis(self, paths):
        """
        Executes analysis for each file path.
        Displays a cancelable progress dialog and aggregates results.
        """
        
        output = []
        total = len(paths)

         # Nothing to analyze
        if total == 0:
            return

        # Progress dialog for user feedback and cancel support
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
            # Keep UI responsive
            QtWidgets.QApplication.processEvents()
            
            # Allow user to cancel analysis
            if progress.wasCanceled():
                output.append("Analysis canceled by user.")
                break

            progress.setValue(i)

            # Skip invalid paths
            if not os.path.isfile(path):
                continue

            # Run model analysis (external logic)
            report = analyze_model(path)

            output.append("Model: {}".format(path))

            # Append per-mesh statistics
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
            # Append reported errors
            for err in report["errors"]:
                output.append("  ERROR: {}".format(err))

            output.append("")
        # Finalize progress UI
        progress.setValue(total)
        progress.close()

        # Display formatted output in dialog
        self.text.setPlainText("\n".join(output))


def show_analyze_panel(file_paths, parent=None):
    """
    Convenience function to display the analysis dialog.
    Blocks execution until the dialog is closed.
    """
    dlg = AnalyzeDialog(file_paths, parent)
    dlg.exec()
