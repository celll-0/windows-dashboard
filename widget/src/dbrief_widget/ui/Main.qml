// Root window. Frameless, stay-on-bottom desktop widget.
// Binds everything to `bridge.model`, which Python pushes on each poll.
import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: win
    width: 390
    height: root.implicitHeight + 24
    visible: true
    color: "transparent"
    title: "Investments"
    flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnBottomHint | Qt.NoDropShadowWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus

    Rectangle {
        anchors.fill: parent
        radius: 6
        color: '#313b3c36'
        border.color: '#c7494945'
        border.width: 0.5
    }

    // The single binding surface to Python. Re-evaluates on modelChanged.
    property var m: bridge.model
    property var positionsList: bridge.positions
    property var newsFeedList: bridge.newsFeed

    ColumnLayout {
        id: root
        x: 16
        y: 12
        width: win.width - 32
        spacing: 10

        // ---- Top section: total value + P/L column -----------------------
        ColumnLayout {
            spacing: 0
            Layout.fillWidth: true

            Text {
                text: "Total value"
                font.pixelSize: 12
                font.weight: Font.Bold
                color: "#B6B7AF"
                bottomPadding: 7
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 46

                // Left: big total value + 24h / ROR stats
                ColumnLayout {
                    Layout.alignment: Qt.AlignTop
                    spacing: 0

                    Text {
                        text: m.totalValue
                        font.pixelSize: 32
                        font.weight: Font.Bold
                        color: "#E4E3DD"
                        bottomPadding: 5
                    }
                    RowLayout {
                        spacing: 20
                        StatItem {
                            label: "LAST 24H"
                            value: m.last24h
                            valueColor: m.last24hColor
                        }
                        StatItem {
                            label: "ROR"
                            value: m.ror
                            valueColor: m.rorColor
                        }
                    }
                }

                // Right: profit / loss column
                PLColumn {
                    Layout.alignment: Qt.AlignTop
                    Layout.fillWidth: true
                    totalPl: m.totalPl
                    totalPlColor: m.totalPlColor
                    totalPlArrow: m.totalPlArrow
                    unrealizedPl: m.unrealizedPl
                    unrealizedColor: m.unrealizedColor
                    realizedPl: m.realizedPl
                    realizedColor: m.realizedColor
                }
            }

            Rectangle {
                Layout.topMargin: 8
                Layout.fillWidth: true
                implicitHeight: 1
                color: "#88C9CAC3"
            }
        }

        // ---- Bottom metric cards ----------------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            MetricCard { label: "Current value"; value: m.currentValue }
            MetricCard { label: "Total cost";    value: m.totalCost }
            MetricCard { label: "Free cash";      value: m.freeCash }
        }

        // ---- Timestamp ---------------------------------------------------
        Text {
            Layout.topMargin: 4
            text: m.updatedText
            font.pixelSize: 10
            color: m.updatedText.startsWith("Error") ? m.updatedColor : "#A5A69E"
        }

        // ---- Top movers ----------------------------------------------------
        MoversSection {
            Layout.fillWidth: true
            Layout.topMargin: 4
            positions: positionsList
        }

        // ---- News feed -------------------------------------------------
        NewsFeedSection {
            Layout.fillWidth: true
            Layout.topMargin: 4
            items: newsFeedList
        }
    }
}
