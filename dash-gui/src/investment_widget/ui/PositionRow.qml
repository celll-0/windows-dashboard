// One row in the Top Movers section: instrument name, a value/price figure
// (toggled by the section's header control), and P/L beneath it.
import QtQuick
import QtQuick.Layouts

RowLayout {
    property string name: "—"
    property string currentValue: "—"
    property string price: "—"
    property bool showPrice: false
    property string pl: "—"
    property color plColor: "#A8AAA2"
    property string plArrow: ""

    spacing: 8

    Text {
        text: name
        font.pixelSize: 13
        font.weight: Font.DemiBold
        color: "#ECEBE5"
        elide: Text.ElideRight
        Layout.fillWidth: true
        leftPadding: 1
        bottomPadding: 2
    }

    RowLayout {
        spacing: 4
        Layout.alignment: Qt.AlignRight

        Text {
            text: showPrice ? price : currentValue
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: "#ECEBE5"
        }
        Text {
            text: "/"
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: "#9FA197"
        }
        Text {
            text: plArrow + " " + pl
            font.pixelSize: 10
            font.weight: Font.DemiBold
            color: plColor
        }
    }
}
