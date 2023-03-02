#ifndef DOUBLEPIPECONNECTIONLENGTHDIALOGBOX_H
#define DOUBLEPIPECONNECTIONLENGTHDIALOGBOX_H

#include <QDialog>

namespace Ui {
class doublePipeConnectionLengthDialogBox;
}

class doublePipeConnectionLengthDialogBox : public QDialog
{
    Q_OBJECT

public:
    explicit doublePipeConnectionLengthDialogBox(QWidget *parent = nullptr);
    ~doublePipeConnectionLengthDialogBox();

private:
    Ui::doublePipeConnectionLengthDialogBox *ui;
};

#endif // DOUBLEPIPECONNECTIONLENGTHDIALOGBOX_H
