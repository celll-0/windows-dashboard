// Always-visible news feed section beneath the movers section. Unlike
// MoversSection this has no expand/collapse control -- headlines should
// always be visible. The list viewport is sized to exactly 5 rows (see
// heightProbe below); scroll (wheel/drag) to see any items beyond that.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: section
    property var items: []

    spacing: 8

    Text {
        text: "News"
        font.pixelSize: 12
        font.weight: Font.Bold
        color: "#9FA197"
    }

    // Invisible, unlaid-out (visible: false) NewsItemRow fed representative
    // content -- a one-line title, and a description long enough that its
    // maximumLineCount: 2 caps it at two lines -- so list.height below
    // tracks NewsItemRow's actual layout (paddings, spacing, date/url lines)
    // rather than a hand-picked pixel guess.
    NewsItemRow {
        id: heightProbe
        visible: false
        width: list.width
        title: "Sample headline for row sizing"
        occurred: "01 Jan, 00:00:00"
        description: "Sample description text long enough to wrap onto two full lines so the probe row's height matches a typical feed item card."
        url: "https://example.com/sample"
        isLast: false
    }

    ListView {
        id: list
        Layout.fillWidth: true
        Layout.preferredHeight: heightProbe.implicitHeight * 5
        clip: true
        spacing: 0
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AlwaysOff }
        model: section.items

        delegate: NewsItemRow {
            width: list.width
            title: modelData.title
            url: modelData.url
            occurred: modelData.occurred
            description: modelData.description
            isLast: index === section.items.length - 1
        }
    }
}
