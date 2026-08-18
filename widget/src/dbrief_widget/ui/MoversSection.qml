// Collapsible movers section beneath the main summary content. The bold
// line/equals glyph (occupying the space a "Top movers" header would have)
// toggles expand/collapse; the label beside it toggles every row between
// showing current value and stock price. Both highlight on hover.
import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: section
    property var positions: []
    property bool expanded: true
    property bool showPrice: false

    spacing: 4

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        Text {
            text: section.expanded ? "=" : "-"
            font.pixelSize: 14
            font.weight: Font.Bold
            color: expandArea.containsMouse ? "#ECEBE5" : "#9FA197"
            Layout.fillWidth: true

            Behavior on color {
                ColorAnimation { duration: animationDurationMs }
            }

            MouseArea {
                id: expandArea
                anchors.fill: parent
                anchors.margins: -4
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: section.expanded = !section.expanded
            }
        }

        Text {
            visible: section.expanded
            text: section.showPrice ? "prc." : "val."
            font.pixelSize: 10
            color: priceArea.containsMouse ? "#ECEBE5" : "#9FA197"

            Behavior on color {
                ColorAnimation { duration: animationDurationMs }
            }

            MouseArea {
                id: priceArea
                anchors.fill: parent
                anchors.margins: -4
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: section.showPrice = !section.showPrice
            }
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        Layout.preferredHeight: section.expanded ? implicitHeight : 0
        clip: true
        spacing: 0

        Behavior on Layout.preferredHeight {
            NumberAnimation { duration: animationDurationMs }
        }

        Repeater {
            model: section.positions

            delegate: ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                PositionRow {
                    Layout.fillWidth: true
                    Layout.bottomMargin: index < section.positions.length - 1 ? 8 : 0
                    name: modelData.name
                    currentValue: modelData.currentValue
                    price: modelData.price
                    showPrice: section.showPrice
                    pl: modelData.pl
                    plColor: modelData.plColor
                    plArrow: modelData.plArrow
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.bottomMargin: index < section.positions.length - 1 ? 8 : 0
                    implicitHeight: 1
                    color: "#88C9CAC3"
                    visible: index < section.positions.length - 1
                }
            }
        }
    }
}
