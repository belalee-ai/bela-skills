#!/usr/bin/env swift
import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    print("Usage: ocr_image.swift <image-path> [<image-path> ...]")
    exit(1)
}

func ocr(path: String) -> String {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        return "ERROR: cannot load \(path)"
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do {
        try handler.perform([req])
        let results = req.results ?? []
        return results.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
    } catch {
        return "ERROR: \(error)"
    }
}

for path in CommandLine.arguments.dropFirst() {
    print("=== \(path) ===")
    print(ocr(path: path))
    print()
}
