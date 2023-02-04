# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TOMsSnapTrace
                                 A QGIS plugin
 snap and trace functions for TOMs. NB Relies to having single type geometries
                              -------------------
        begin                : 2017-12-15
        git sha              : $Format:%H$
        copyright            : (C) 2017 by TH
        email                : th@mhtc.co.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os.path, math
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QAction,
    QDialogButtonBox,
    QLabel,
    QDockWidget, QTableView, QGridLayout, QVBoxLayout, QDialog, QWidget, QHeaderView, QItemDelegate
)

from qgis.PyQt.QtGui import (
    QIcon,
    QPixmap
)

from qgis.PyQt.QtCore import (
    QObject, QTimer, pyqtSignal,
    QTranslator,
    QSettings,
    QCoreApplication,
    qVersion, Qt, QAbstractTableModel
)

from qgis.PyQt.QtSql import (
    QSqlDatabase, QSqlQuery, QSqlQueryModel, QSqlRelation,  QSqlTableModel, QSqlRelationalTableModel, QSqlRelationalDelegate, QSqlTableModel
)

from qgis.core import (
    Qgis,
    QgsExpressionContextUtils,
    QgsProject,
    QgsMessageLog,
    QgsFeature,
    QgsGeometry,
    QgsApplication, QgsCoordinateTransform, QgsCoordinateReferenceSystem,
    QgsGpsDetector, QgsGpsConnection, QgsGpsInformation, QgsPoint, QgsPointXY,
    QgsDataSourceUri, QgsCredentials
)

# Initialize Qt resources from file resources.py
from resources import *

# Import the code for the dialog

from TOMs.core.TOMsMessageLog import TOMsMessageLog
from TOMs.restrictionTypeUtilsClass import TOMsConfigFile

from demandVRMsForm.demand_VRMs_UtilsClass import DemandUtilsMixin

class time_periods_controlled_during_survey_hours(DemandUtilsMixin):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        DemandUtilsMixin.__init__(self, iface)

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Set up local logging
        loggingUtils = TOMsMessageLog()
        loggingUtils.setLogFile()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Controlled Hours For Survey')
        # TODO: We are going to let the user set this up in a future iteration
        #self.toolbar = self.iface.addToolBar(u'TOMsSnapTrace')
        #self.toolbar.setObjectName(u'TOMsSnapTrace')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Controlled Hours For Survey', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        # Create the dialog (after translation) and keep reference
        #self.dlg = TOMsSnapTraceDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        #if add_to_toolbar:
        #    self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/TOMsSnapTrace/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Controlled Hours For Survey'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Controlled Hours For Survey'),
                action)
            #self.iface.removeToolBarIcon(action)
        # remove the toolbar
        #del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        """ Start """
        try:
            self.dbConn, self.demand_schema = self.getDbConn('TimePeriodsControlledDuringSurveyHours')
        except Exception as e:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Connection issue"), self.tr("Issue finding db or TimePeriodsControlledDuringSurveyHours layer")
                              )
            TOMsMessageLog.logMessage('time_periods_controlled_during_survey_hours: error in getting db connection: {}'.format(e),
                                      level=Qgis.Warning)
            return False

        TOMsMessageLog.logMessage("In enableDemandToolbarItems. schema: {}".format(self.demand_schema), level=Qgis.Warning)

        if not self.dbConn.open():
            reply = QMessageBox.information(None, "Error",
                                            "Unable to establish a database connection - {} {}\n\n".format(self.dbConn.lastError().type(), self.dbConn.lastError().databaseText()), QMessageBox.Ok)
            return False

        controlHoursForm = controlHoursWidget(self.dbConn, self.demand_schema)
        controlHoursForm.populateWidget()

        layout = QVBoxLayout()
        layout.addWidget(controlHoursForm)

        self.form = QDialog()

        buttonBox = QDialogButtonBox(self.form)
        buttonBox.setStandardButtons(QDialogButtonBox.Cancel |
                                          QDialogButtonBox.Ok)
        #button_box = QDialogButtonBox(
        #    QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.form.accept)
        buttonBox.rejected.connect(self.form.reject)

        layout.addWidget(buttonBox)

        self.form.setLayout(layout)

        self.form.setWindowTitle("Control Hours for Surveys")
        self.form.setGeometry(100, 100, 300, 400)

        TOMsMessageLog.logMessage("In controlHoursForm. finished setting up ...",
                                  level=Qgis.Warning)

        self.form.show()
        #return form

class controlHoursWidget(QTableView):

    def __init__(self, dbConn, demand_schema):
        super(controlHoursWidget, self).__init__()
        TOMsMessageLog.logMessage("In controlHoursWidget:init ... ", level=Qgis.Warning)
        self.dbConn = dbConn
        self.demand_schema = demand_schema

        self.model = thisTableModel(self, db=self.dbConn)

    def populateWidget(self):

        TOMsMessageLog.logMessage("In controlHoursWidget:populateControlHoursWidget ... ", level=Qgis.Warning)

        table = '"{}"."TimePeriodsControlledDuringSurveyHours"'.format(self.demand_schema)
        self.model.setTable(table)

        self.model.setJoinMode(QSqlRelationalTableModel.LeftJoin)
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        #self.model.orderByClause("BeatTitle, Description")  ### TODO: NOt working ...
        self.model.setSort(int(self.model.fieldIndex("BeatTitle")), Qt.AscendingOrder)

        self.model.setRelation(int(self.model.fieldIndex("SurveyID")),
                                  QSqlRelation('demand' + '.\"Surveys\"', '\"SurveyID\"', '\"BeatTitle\"'))

        self.model.setRelation(int(self.model.fieldIndex("TimePeriodID")),
                                  QSqlRelation('toms_lookups' + '.\"TimePeriods\"', '\"Code\"', '\"Description\"'))

        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        self.model.select()

        self.setModel(self.model)

        self.setColumnHidden(self.model.fieldIndex("gid"), True)
        self.setItemDelegateForColumn(self.model.fieldIndex("BeatTitle"), readOnlyDelegate(self));
        self.setItemDelegateForColumn(self.model.fieldIndex("Description"), readOnlyDelegate(self));

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


# https://stackoverflow.com/questions/24024815/set-a-whole-column-in-qtablewidget-read-only-in-python
class readOnlyDelegate(QItemDelegate):
    def createEditor(self, *args):
        return None

class thisTableModel(QSqlRelationalTableModel):
    #https://stackoverflow.com/questions/48193325/checkbox-in-qlistview-using-qsqltablemodel
    def __init__(self, *args, **kwargs):
        QSqlRelationalTableModel.__init__(self, *args, **kwargs)
        self.checkable_data = {}

    def flags(self, index):
        fl = QSqlRelationalTableModel.flags(self, index)
        if index.column() == self.fieldIndex("Controlled"):
            fl |= Qt.ItemIsUserCheckable
        return fl

    """
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.CheckStateRole and (
            self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags
        ):
            if index.row() not in self.checkable_data.keys():
                self.setData(index, Qt.Unchecked, Qt.CheckStateRole)
            return self.checkable_data[index.row()]
        else:
            return QSqlRelationalTableModel.data(self, index, role)

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and (
            self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags
        ):
            self.checkable_data[index.row()] = value
            self.dataChanged.emit(index, index, (role,))
            return True
        return QSqlRelationalTableModel.setData(self, index, value, role)
    """

class controlHoursForm(QDialog):
    def __init__(self, parent=None):
        super(controlHoursForm, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        TOMsMessageLog.logMessage("In controlHoursForm. setting up ...",
                                  level=Qgis.Warning)
        view = QTableView()
        view.setObjectName("hours_table_view")
        layout = QGridLayout()
        layout.addWidget(view)

        form = QDialog()
        form.setLayout(layout)

        form.setWindowTitle("Control Hours for Surveys")
        form.setGeometry(100, 100, 300, 400)

        TOMsMessageLog.logMessage("In controlHoursForm. finished setting up ...",
                                  level=Qgis.Warning)

"""

class TableModel(QSqlTableModel):

    def __init__(self, data, checked):
        super(TableModel, self).__init__()
        self._data = data
        self._checked = checked

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)

        if role == Qt.CheckStateRole:
            checked = self._checked[index.row()][index.column()]
            return Qt.Checked if checked else Qt.Unchecked

    def setData(self, index, value, role):
        if role == Qt.CheckStateRole:
            checked = value == Qt.Checked
            self._checked[index.row()][index.column()] = checked
            return True

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsUserCheckable

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()


        self.table = QtWidgets.QTableView()

        data = [
          [1, 9, 2],
          [1, 0, -1],
          [3, 5, 2],
          [3, 3, 2],
          [5, 8, 9],
        ]

        checked = [
          [True, True, True],
          [False, False, False],
          [True, False, False],
          [True, False, True],
          [False, True, True],
        ]

        self.model = TableModel(data, checked)
        self.table.setModel(self.model)

        self.setCentralWidget(self.table)

"""