## Trnsys GUI
### Getting started
#### Prerequisites
Python 3.5 and PyQt (for example installed with Anaconda).
#### Installing
Clone the repository and run TrnsysGUI/trnsysGUI/core.py
### Running the tests
#### Dev Notes
A diagram has Blocks and Connections.
Each Block has two lists, inputs and outputs, of PortItems.

Connections go from a _fromPort_ PortItem to a _toPort_ PortItem.

The editor has two modes: One, in which the connection can be clicked and dragged to form segments, and one which mantains 
always 90 degree angles.
 
The underlying structure of the visual connections is a double linked list, and each connection has a sorted list of 
segments and a method to get the nodes in order.

Nodes know their previous and next nodes.
They can have either a cornerItem or a connection as parent.
In the latter case, they are either at the Ports or at a _disrupted segment_
To update the segments adjacent to a corner, two methods can be used:
* Check the neighborhood of the segments for corners/ports
* Use the index of the nodes and segments

The gradient of a connection is a full interpolation between start and end color.

The diagramEditor also has a list of Groups, which contain a list of Connections and Blocks, _groupList_. One can create new groups, name them and they appear as loop in the trnsys export.

##### Usage notes:
- Dont drag on a line and release afterwards on the line (segment will break)

##### Shortcuts
- "c"       : start copying
- "v"       : paste
- "s"       : start selecting multiple items
- "Ctrl+d"  : Delete selection
- "m"       : Toggle editor/connection mode