from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, QPointF, QTimer
import numpy as np
import sys
import cv2
import os
from ui.video_ui import Ui_video_widget
import pandas as pd
from utils.vis_image import ImageDrawer
from utils.selector import PersonSelector
from cv_utils.cv_control import VideoLoader, JsonLoader
from skeleton.detect_skeleton import PoseEstimater
from utils.model import Model

class PoseVideoTabControl(QWidget):
    def __init__(self, model:Model, parent = None):
        super(PoseVideoTabControl, self).__init__(parent)
        self.ui = Ui_video_widget()
        self.ui.setupUi(self)
        self.model = model
        self.setupComponents()
        self.init_var()
        self.bind_ui()

    def bind_ui(self):
        self.ui.loadOriginalVideoBtn.clicked.connect(
            lambda: self.loadVideo(is_processed=False))
        self.ui.loadProcessedVideoBtn.clicked.connect(
            lambda: self.loadVideo(is_processed=True))

        self.ui.playBtn.clicked.connect(self.play_btn_clicked)
        self.ui.backKeyBtn.clicked.connect(
            lambda: self.ui.frameSlider.setValue(self.ui.frameSlider.value() - 1)
        )
        self.ui.forwardKeyBtn.clicked.connect(
            lambda: self.ui.frameSlider.setValue(self.ui.frameSlider.value() + 1)
        )
        self.ui.frameSlider.valueChanged.connect(self.analyzeFrame)
        self.ui.FrameView.mousePressEvent = self.mousePressEvent
        self.ui.startCodeBtn.clicked.connect(self.toggleDetect)
        self.ui.selectCheckBox.stateChanged.connect(self.toggleSelect)
        self.ui.showSkeletonCheckBox.stateChanged.connect(self.toggleShowSkeleton)
        self.ui.showBboxCheckBox.stateChanged.connect(self.toggleShowBbox)

    def mousePressEvent(self, event):
        view_rect = self.ui.FrameView.rect()
        pos = event.pos()

        if not view_rect.contains(pos):
            return
        search_person_df = self.pose_estimater.getPersonDf(frame_num = self.ui.frameSlider.value())
        scene_pos = self.ui.FrameView.mapToScene(pos)
        x, y = scene_pos.x(), scene_pos.y()

        if self.ui.selectCheckBox.isChecked():
            if event.button() == Qt.LeftButton:
                self.person_selector.select(x, y, search_person_df)
                self.pose_estimater.setPersonId(self.person_selector.selected_id)

        if self.label_kpt:
            if event.button() == Qt.LeftButton:
                self.sendtoTable(x, y, 1)
            elif event.button() == Qt.RightButton:
                self.sendtoTable(0, 0, 0)
            self.label_kpt = False

        self.updateFrame(self.ui.frameSlider.value())

    def keyPressEvent(self, event):
        if event.key() == ord('D') or event.key() == ord('d'):
            self.ui.frameSlider.setValue(self.ui.frameSlider.value() + 1)
        elif event.key() == ord('A') or event.key() == ord('a'):
            self.ui.frameSlider.setValue(self.ui.frameSlider.value() - 1)
        else:
            super().keyPressEvent(event)

    def setupComponents(self):
        self.person_selector = PersonSelector()
        self.pose_estimater = PoseEstimater(self.model)
        self.kpt_dict = self.pose_estimater.joints["haple"]["keypoints"]
        self.image_drawer = ImageDrawer(self.pose_estimater)
        self.video_loader = VideoLoader(self.image_drawer)

    def init_var(self):
        self.is_play = False
        self.video_scene = QGraphicsScene()
        self.video_scene.clear()
        self.correct_kpt_idx = 0
        self.label_kpt = False
        self.is_processed = False

    def reset(self):
        self.person_selector.reset()
        self.pose_estimater.reset()
        self.image_drawer.reset()
        self.video_scene.clear()

    def loadVideo(self, is_processed:bool = False):
        if self.is_play:
            self.ui.playBtn.click()
        self.is_processed = is_processed
        self.video_loader.loadVideo()
        self.checkVideoLoad()

    def checkVideoLoad(self):
        if not self.video_loader.video_name:
            return
        if self.video_loader.is_loading:
            self.ui.videoNameLabel.setText("讀取影片中")
            QTimer.singleShot(100, self.checkVideoLoad)
            return
        self.updateVideoInfo()

    def updateVideoInfo(self):
        self.reset()
        self.initFrameSlider()
        self.updateFrame(0)
        self.model.setImageSize(self.video_loader.video_size)
        self.ui.videoNameLabel.setText(self.video_loader.video_name)
        video_size = self.video_loader.video_size
        self.ui.ResolutionLabel.setText(f"(0,0) - {video_size[0]} x {video_size[1]}")
        if self.is_processed:
            self.loadProcessedData()

    def loadProcessedData(self):
        json_loader = JsonLoader(self.video_loader.folder_path, self.video_loader.video_name)
        person_df, bat_df, SwingData_df = json_loader.load()
        if not person_df.empty and not bat_df.empty and not SwingData_df.empty:
            self.pose_estimater.setProcessedData(person_df, bat_df)
            self.ui.showSkeletonCheckBox.setChecked(True)

    def initFrameSlider(self):
        total_frames = self.video_loader.total_frames
        self.ui.frameSlider.setMinimum(0)
        self.ui.frameSlider.setMaximum(total_frames - 1)
        self.ui.frameSlider.setValue(0)
        self.ui.frameNumLabel.setText(f'0/{total_frames - 1}')

    def showImage(self, image: np.ndarray, scene: QGraphicsScene, GraphicsView: QGraphicsView):
        scene.clear()
        image = image.copy()
        image = cv2.circle(image, (0, 0), 10, (0, 0, 255), -1)
        w, h = image.shape[1], image.shape[0]
        bytesPerline = 3 * w
        qImg = QImage(image, w, h, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        scene.addPixmap(pixmap)
        GraphicsView.setScene(scene)
        GraphicsView.setAlignment(Qt.AlignLeft)
        GraphicsView.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)

    def playFrame(self, start_num=0):
        for i in range(start_num, self.video_loader.total_frames):
            if not self.is_play:
                break
            self.ui.frameSlider.setValue(i)
            if i == self.video_loader.total_frames - 1 and self.is_play:
                self.play_btn_clicked()
            cv2.waitKey(15)

    def play_btn_clicked(self):
        if self.video_loader.video_name == "":
            QMessageBox.warning(self, "無法播放影片", "請讀取影片!")
            return
        if self.video_loader.is_loading:
            QMessageBox.warning(self, "影片讀取中", "請稍等!")
            return
        self.is_play = not self.is_play
        self.ui.playBtn.setText("||" if self.is_play else "▶︎")
        if self.is_play:
            self.playFrame(self.ui.frameSlider.value())

    def analyzeFrame(self):
        frame_num = self.ui.frameSlider.value()
        self.ui.frameNumLabel.setText(f'{frame_num}/{len(self.video_loader.video_frames) - 1}')
        frame = self.video_loader.getVideoImage(frame_num)
        _, _, fps, _ = self.pose_estimater.detectKpt(frame, frame_num, is_video=True, is_processed=self.is_processed)
        self.ui.FPSInfoLabel.setText("280")
        if not self.is_processed and frame_num == self.video_loader.total_frames - 1:
            self.video_loader.saveVideo(False)
            self.video_loader.saveVideo(True)
        self.updateFrame(frame_num)

    def updateFrame(self, frame_num:int):
        image = self.video_loader.getVideoImage(frame_num)
        drawed_img = self.image_drawer.drawInfo(image, frame_num, self.pose_estimater.kpt_buffer)
        self.showImage(drawed_img, self.video_scene, self.ui.FrameView)

    def toggleDetect(self):
        self.ui.showSkeletonCheckBox.setChecked(True)
        frame = self.video_loader.getVideoImage(0)
        _, _, _, _ = self.pose_estimater.detectKpt(frame, 0, is_video=True)
        self.ui.playBtn.click()

    def toggleSelect(self, state:int):
        if not self.ui.showSkeletonCheckBox.isChecked():
            self.ui.selectCheckBox.setCheckState(0)
            QMessageBox.warning(self, "無法選擇人", "請選擇顯示人體骨架!")
            return
        if state == 2:
            self.person_selector.select(search_person_df=self.pose_estimater.getPersonDf(frame_num=self.ui.frameSlider.value()))
            self.pose_estimater.setPersonId(self.person_selector.selected_id)
        else:
            self.pose_estimater.setPersonId(None)
        self.updateFrame(self.ui.frameSlider.value())

    def toggleShowSkeleton(self, state:int):
        if state == 2:
            self.pose_estimater.setDetect(True)
            self.image_drawer.setShowSkeleton(True)
        else:
            self.pose_estimater.setDetect(False)
            self.image_drawer.setShowSkeleton(False)
        self.updateFrame(self.ui.frameSlider.value())

    def toggleShowBbox(self, state:int):
        if state == 2:
            self.image_drawer.setShowBbox(True)
        else:
            self.image_drawer.setShowBbox(False)

    def clearTableView(self):
        self.ui.KptTable.clear()
        self.ui.KptTable.setColumnCount(4)
        title = ["關節點", "X", "Y", "有無更改"]
        self.ui.KptTable.setHorizontalHeaderLabels(title)
        header = self.ui.KptTable.horizontalHeader()
        for i in range(4):
            header.setDefaultAlignment(Qt.AlignLeft)

    def importDatatoTable(self, frame_num:int):
        self.clearTableView()
        person_id = self.pose_estimater.person_id
        if person_id is None:
            return
        person_data = self.pose_estimater.getPersonDf(frame_num=frame_num, is_select=True)
        if person_data.empty:
            self.clearTableView()
            self.ui.selectCheckBox.setChecked(False)
            return

        num_keypoints = len(self.kpt_dict)
        if self.ui.KptTable.rowCount() < num_keypoints:
            self.ui.KptTable.setRowCount(num_keypoints)

        for kpt_idx, kpt in enumerate(person_data['keypoints'].iloc[0]):
            kptx, kpty, kpt_label = kpt[0], kpt[1], kpt[3]
            kpt_name = self.kpt_dict[kpt_idx]
            kpt_name_item = QTableWidgetItem(str(kpt_name))
            kptx_item = QTableWidgetItem(str(np.round(kptx,1)))
            kpty_item = QTableWidgetItem(str(np.round(kpty,1)))
            if kpt_label :
                kpt_label_item = QTableWidgetItem("Y")
            else:
                kpt_label_item = QTableWidgetItem("N")
            kpt_name_item.setTextAlignment(Qt.AlignRight)
            kptx_item.setTextAlignment(Qt.AlignRight)
            kpty_item.setTextAlignment(Qt.AlignRight)
            kpt_label_item.setTextAlignment(Qt.AlignRight)
            self.ui.KptTable.setItem(kpt_idx, 0, kpt_name_item)
            self.ui.KptTable.setItem(kpt_idx, 1, kptx_item)
            self.ui.KptTable.setItem(kpt_idx, 2, kpty_item)
            self.ui.KptTable.setItem(kpt_idx, 3, kpt_label_item)

    def onCellClicked(self, row, column):
        self.correct_kpt_idx = row
        self.label_kpt = True

    def sendtoTable(self, kptx:float, kpty:float, kpt_label:int):
        kptx_item = QTableWidgetItem(str(kptx))
        kpty_item = QTableWidgetItem(str(kpty))
        if kpt_label :
            kpt_label_item = QTableWidgetItem("Y")
        else:
            kpt_label_item = QTableWidgetItem("N")
        kptx_item.setTextAlignment(Qt.AlignRight)
        kpty_item.setTextAlignment(Qt.AlignRight)
        kpt_label_item.setTextAlignment(Qt.AlignRight)
        self.ui.KptTable.setItem(self.correct_kpt_idx, 1, kptx_item)
        self.ui.KptTable.setItem(self.correct_kpt_idx, 2, kpty_item)
        self.ui.KptTable.setItem(self.correct_kpt_idx, 3, kpt_label_item)

        self.pose_estimater.update_person_df(kptx, kpty, self.ui.frameSlider.value(), self.correct_kpt_idx)
        self.updateFrame(frame_num=self.ui.frameSlider.value())

    def correctId(self):
        before_correctId = self.ui.beforeCorrectId.value()
        after_correctId = self.ui.afterCorrectId.value()
        self.pose_estimater.correct_person_id(before_correctId, after_correctId)
        self.updateFrame(self.ui.frameSlider.value())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PoseVideoTabControl()
    window.show()
    sys.exit(app.exec_())
