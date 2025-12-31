import React from "react";
import { FileCheck, Code, Github, Mail } from "lucide-react";

const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
            <FileCheck className="w-10 h-10 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              智能合同处理自动化系统
            </h1>
            <p className="text-gray-500 mt-1">
              Contract Processing Automation System
            </p>
          </div>
        </div>

        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              系统简介
            </h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              智能合同处理自动化系统是一个基于 AI 技术的合同审查和处理平台，旨在帮助企业自动化合同处理流程，提高工作效率，降低法律风险。
            </p>
            <p className="text-gray-700 leading-relaxed">
              系统支持文档解析、合规校验、风险评估等功能，可以快速识别合同中的潜在风险，并提供专业的处理建议。
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              主要功能
            </h2>
            <ul className="space-y-3 text-gray-700">
              <li className="flex items-start gap-3">
                <Code className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <strong className="text-gray-900">文档解析</strong>
                  <p className="text-gray-600 text-sm mt-1">
                    支持 PDF、DOCX 等多种格式，自动提取合同文本内容
                  </p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <Code className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <strong className="text-gray-900">风险评估</strong>
                  <p className="text-gray-600 text-sm mt-1">
                    智能分析合同风险等级，识别法律、财务等多维度风险
                  </p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <Code className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <strong className="text-gray-900">合规校验</strong>
                  <p className="text-gray-600 text-sm mt-1">
                    自动检查合同条款是否符合相关法律法规
                  </p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <Code className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <strong className="text-gray-900">自动化流程</strong>
                  <p className="text-gray-600 text-sm mt-1">
                    基于 N8N 工作流引擎，实现合同处理的自动化流程
                  </p>
                </div>
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              技术栈
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">前端</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• React + TypeScript</li>
                  <li>• Tailwind CSS</li>
                  <li>• React Router</li>
                  <li>• Axios</li>
                </ul>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">后端</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• FastAPI (Python)</li>
                  <li>• LLM 集成</li>
                  <li>• N8N 工作流</li>
                  <li>• 工具调用框架</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              联系我们
            </h2>
            <div className="flex items-center gap-4 text-gray-700">
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-blue-600" />
                <span>如有问题或建议，欢迎联系我们</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;

