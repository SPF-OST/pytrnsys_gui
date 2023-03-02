#include "doublepipeconnectionlengthdialogbox.h"
#include "ui_doublepipeconnectionlengthdialogbox.h"

doublePipeConnectionLengthDialogBox::doublePipeConnectionLengthDialogBox(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::doublePipeConnectionLengthDialogBox)
{
    ui->setupUi(this);
}

doublePipeConnectionLengthDialogBox::~doublePipeConnectionLengthDialogBox()
{
    delete ui;
}
