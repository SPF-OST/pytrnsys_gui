## Trnsys GUI
####Getting started
#####Prerequisites
Python 3.5 and PyQt (for example installed with Anaconda):

conda create -n myenv python=3.5

conda activate myenv

conda install pyqt5

#####Installing
Clone the repository and run TrnsysGUI/trnsysGUI/core.py
#####Dev Notes
General structure
A diagram has Blocks and Connections.
Each Block has two lists, inputs and outputs, of PortItems.

Connections go from a _fromPort_ PortItem to a _toPort_ PortItem.

The editor has two modes: One, in which the connection can be clicked and dragged to form segments, and one which mantains 
always 90 degree angles. Mode one is disabled.
 
The underlying structure of the visual connections is a double linked list, and Connection has a sorted list of 
segments and a method to get the nodes in order.

Nodes know their previous and next nodes.
They can have either a cornerItem or a Connection as parent.
If the parent is a Connection, then the node belongs to a PortItem

The gradient of a connection is a full interpolation between start and end color.

The diagramEditor also has a list of Groups, which contain a list of Connections and Blocks, _groupList_. 
One can create new groups, name them and they appear as loop in the trnsys export. Also, one can inspect which blocks 
are in which group.



######Shortcuts
- "c"       : start copying
- "v"       : paste
- "s"       : start selecting multiple items
- "Ctrl+d"  : Delete selection
- "ctrl+m"  : Move Storage direct ports
- "ctrl+z"  : Undo (few actions allowed)
- "ctrl+y"  : Redo
- "a"       : Toggle snap grid
- "q"       : Start align mode
