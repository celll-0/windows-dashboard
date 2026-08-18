// One row in the news feed: full title (always shown in full, wraps rather
// than eliding), a date, and a truncated description. The whole card is
// clickable -- opens `url` in the system browser. On hover: the background
// lightens, the title underlines, and a faded url preview fades in (kept in
// layout at all times so the card doesn't resize/jump while hovering).
import QtQuick
import QtQuick.Layouts

Item {
    id: row

    property string title: "—"
    property string url: ""
    property string occurred: "—"
    property string description: ""
    property bool isLast: false

    readonly property int verticalPadding: 6

    implicitWidth: content.implicitWidth
    implicitHeight: content.implicitHeight + verticalPadding * 2

    Rectangle {
        id: hoverBackground
        anchors.fill: parent
        radius: 4
        color: hoverArea.containsMouse ? "#0CFFFFFF" : "transparent"

        Behavior on color {
            ColorAnimation { duration: animationDurationMs }
        }
    }

    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: row.verticalPadding
        spacing: 2

        Text {
            text: row.title
            font.pixelSize: 13
            font.weight: Font.Bold
            font.underline: hoverArea.containsMouse
            color: "#ECEBE5"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            text: row.occurred
            font.pixelSize: 10
            color: "#9FA197"
        }

        Text {
            text: row.description
            font.pixelSize: 11
            color: "#A8AAA2"
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
            Layout.fillWidth: true
            Layout.topMargin: 2
        }

        Text {
            text: row.url
            font.pixelSize: 10
            font.weight: Font.Bold
            font.underline: true
            color: "#73ECEBE5"
            elide: Text.ElideRight
            Layout.fillWidth: true
            Layout.topMargin: 4
            opacity: hoverArea.containsMouse ? 1 : 0

            Behavior on opacity {
                NumberAnimation { duration: animationDurationMs }
            }
        }

        Rectangle {
            visible: !row.isLast
            Layout.fillWidth: true
            Layout.topMargin: 8
            implicitHeight: 1
            color: "#88C9CAC3"
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: row.url.length > 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (row.url.length > 0) Qt.openUrlExternally(row.url)
    }
}
