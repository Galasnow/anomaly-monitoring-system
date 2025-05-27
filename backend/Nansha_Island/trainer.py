import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import datetime
import torch.optim.lr_scheduler as lr_scheduler
from torch.autograd import Variable

class Trainer(object):
    def __init__(self, net, file_path):
        self.file_path = file_path
        print("model save dir:", file_path)
        self.net = net
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

    def train_model(self, train_loader, test_loader, epoch):
        self.net.train()
        print("start train!")
        criterion = nn.BCELoss(reduction='none')  # 保持每个像素的损失
        optimizer = optim.AdamW(self.net.parameters(), lr=1e-4)
        num_training_steps = len(train_loader) * epoch
        num_warmup_steps = int(0.1 * num_training_steps)
        scheduler = lr_scheduler.LambdaLR(optimizer, lr_lambda=lambda epoch: min(1, (epoch + 1) / num_warmup_steps))

        Loss_list = []
        Accuracy_list = []

        for i in range(epoch):
            print("epoch:", i)
            starttime1 = datetime.datetime.now()
            for j, sample in enumerate(train_loader, 0):
                image = Variable(sample["image"], requires_grad=False).cuda()
                label = Variable(sample["label"], requires_grad=False).cuda()

                # 计算 no_data_mask
                no_data_mask = (image == 0).all(dim=1, keepdim=True)

                prediction = self.net(image)

                # 计算损失
                loss = F.binary_cross_entropy(prediction, label, reduction='none')

                # 扩展 no_data_mask 的维度以匹配 loss
                no_data_mask_expanded = no_data_mask.expand_as(loss)

                # 忽略 NoData 像素的损失
                loss[no_data_mask_expanded] = 0

                # 对非 NoData 像素的损失取平均
                valid_pixels = ~no_data_mask_expanded
                if valid_pixels.sum() > 0:
                    loss = loss[valid_pixels].mean()
                else:
                    loss = torch.tensor(0.0, device=loss.device)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                scheduler.step()

            # 计算精度
            prediction = prediction.view(-1)
            label = label.view(-1)
            no_data_mask_expanded = no_data_mask_expanded.view(-1)
            valid_pixels = ~no_data_mask_expanded

            prediction = prediction[valid_pixels]  # 只计算有效像素
            label = label[valid_pixels]

            balance = 0.5
            prediction = torch.ge(prediction, balance).type(torch.cuda.FloatTensor)
            accuracy = torch.eq(label, prediction).type(torch.cuda.FloatTensor)
            accuracy = torch.div(accuracy.sum(), len(label))

            Loss_list.append(loss.item())
            Accuracy_list.append(accuracy.item())
            self.save_model(i)

            endtime1 = datetime.datetime.now()
            # 记录日志
            with open(r'E:\04_ZhongyanExperiment\02_Building\02_Fukche_Base\Train_Durbuk\train.txt', 'a') as f:
                f.write(f"{i} {loss.item()} {accuracy.item()} {(endtime1 - starttime1).seconds}\n")

            print(f"Train-Epoch:{i+1}/{epoch}, loss:{loss.item()}, accuracy:{accuracy.item()}, seconds:{(endtime1 - starttime1).seconds}")

            # 每10个epoch计算一次测试精度
            # if (i+1) % 1 == 0:
            #     self.net.eval()
            #     test_loss = 0
            #     test_accuracy = 0
            #     with torch.no_grad():
            #         for j, sample in enumerate(test_loader, 0):
            #             image = Variable(sample["image"], requires_grad=False).cuda()
            #             label = Variable(sample["label"], requires_grad=False).cuda()
            #             no_data_mask = Variable(sample["no_data_mask"], requires_grad=False).cuda()
            #
            #             prediction = self.net(image)
            #             loss = F.binary_cross_entropy(prediction, label, reduction='none')
            #             no_data_mask_expanded = no_data_mask.expand_as(loss)
            #             loss[no_data_mask_expanded] = 0
            #             valid_pixels = ~no_data_mask_expanded
            #             if valid_pixels.sum() > 0:
            #                 loss = loss[valid_pixels].mean()
            #             else:
            #                 loss = torch.tensor(0.0, device=loss.device)
            #             test_loss += loss
            #
            #             prediction = prediction.view(-1)
            #             label = label.view(-1)
            #             no_data_mask_expanded = no_data_mask_expanded.view(-1)
            #             valid_pixels = ~no_data_mask_expanded
            #
            #             prediction = prediction[valid_pixels]
            #             label = label[valid_pixels]
            #
            #             prediction = torch.ge(prediction, balance).type(torch.cuda.FloatTensor)
            #             tmp_accuracy = torch.eq(label, prediction).type(torch.cuda.FloatTensor)
            #             test_accuracy += torch.div(tmp_accuracy.sum(), len(label))
            #
            #     test_accuracy = torch.div(test_accuracy, len(test_loader))
            #     test_loss = torch.div(test_loss, len(test_loader))
            #
            #     with open(r'E:\04_ZhongyanExperiment\02_Building\Test_all\val.txt', 'a') as t:
            #         t.write(f"{i} {test_loss.item()} {test_accuracy.item()}\n")
            #
            #     print(f"Test-Epoch:{i+1}/{epoch}, loss:{test_loss.item()}, accuracy:{test_accuracy.item()}")

    def save_model(self, epoch):
        torch.save(self.net.state_dict(), f'./model_epoch_{epoch}.pth')
        print(f"Model saved for epoch {epoch}!")

    def restore_model(self):
        print("restore the model...")
        self.net.load_state_dict(torch.load(self.file_path, map_location=self.device))

    def predict(self, image):
        self.net.load_state_dict(torch.load(self.file_path, map_location=self.device, weights_only=True))
        self.net.eval()
        prediction = self.net(image)
        return prediction
