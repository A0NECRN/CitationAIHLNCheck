import random
import os
import re
import json

# Real entries with standard citation keys (AuthorYearKeyword)
REAL_ENTRIES = [
    """@article{vaswani2017attention,
      title={Attention is all you need},
      author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, {\L}ukasz and Polosukhin, Illia},
      journal={Advances in neural information processing systems},
      volume={30},
      year={2017}
    }""",
    """@article{he2016deep,
      title={Deep residual learning for image recognition},
      author={He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
      journal={Proceedings of the IEEE conference on computer vision and pattern recognition},
      pages={770--778},
      year={2016}
    }""",
    """@article{devlin2018bert,
      title={Bert: Pre-training of deep bidirectional transformers for language understanding},
      author={Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina},
      journal={arXiv preprint arXiv:1810.04805},
      year={2018}
    }""",
    """@inproceedings{goodfellow2014generative,
      title={Generative adversarial nets},
      author={Goodfellow, Ian and Pouget-Abadie, Jean and Mirza, Mehdi and Xu, Bing and Warde-Farley, David and Ozair, Sherjil and Courville, Aaron and Bengio, Yoshua},
      booktitle={Advances in neural information processing systems},
      volume={27},
      year={2014}
    }""",
    """@article{kingma2014adam,
      title={Adam: A method for stochastic optimization},
      author={Kingma, Diederik P and Ba, Jimmy},
      journal={arXiv preprint arXiv:1412.6980},
      year={2014}
    }""",
    """@inproceedings{krizhevsky2012imagenet,
      title={Imagenet classification with deep convolutional neural networks},
      author={Krizhevsky, Alex and Sutskever, Ilya and Hinton, Geoffrey E},
      booktitle={Advances in neural information processing systems},
      volume={25},
      year={2012}
    }""",
    """@article{silver2016mastering,
      title={Mastering the game of Go with deep neural networks and tree search},
      author={Silver, David and Huang, Aja and Maddison, Chris J and Guez, Arthur and Sifre, Laurent and Van Den Driessche, George and Schrittwieser, Julian and Antonoglou, Ioannis and Panneershelvam, Veda and Lanctot, Marc and others},
      journal={nature},
      volume={529},
      number={7587},
      pages={484--489},
      year={2016}
    }""",
    """@article{brown2020language,
      title={Language models are few-shot learners},
      author={Brown, Tom and Mann, Benjamin and Ryder, Nick and Subbiah, Melanie and Kaplan, Jared D and Dhariwal, Prafulla and Neelakantan, Arvind and Shyam, Pranav and Sastry, Girish and Askell, Amanda and others},
      journal={Advances in neural information processing systems},
      volume={33},
      pages={1877--1901},
      year={2020}
    }""",
    """@article{dosovitskiy2020image,
      title={An image is worth 16x16 words: Transformers for image recognition at scale},
      author={Dosovitskiy, Alexey and Beyer, Lucas and Kolesnikov, Alexander and Weissenborn, Dirk and Zhai, Xiaohua and Unterthiner, Thomas and Dehghani, Mostafa and Minderer, Matthias and Heigold, Georg and Gelly, Sylvain and others},
      journal={arXiv preprint arXiv:2010.11929},
      year={2020}
    }""",
    """@article{hochreiter1997long,
      title={Long short-term memory},
      author={Hochreiter, Sepp and Schmidhuber, J{\"u}rgen},
      journal={Neural computation},
      volume={9},
      number={8},
      pages={1735--1780},
      year={1997}
    }""",
    """@article{lecun1998gradient,
      title={Gradient-based learning applied to document recognition},
      author={LeCun, Yann and Bottou, L{\'e}on and Bengio, Yoshua and Haffner, Patrick},
      journal={Proceedings of the IEEE},
      volume={86},
      number={11},
      pages={2278--2324},
      year={1998}
    }""",
    """@article{mikolov2013efficient,
      title={Efficient estimation of word representations in vector space},
      author={Mikolov, Tomas and Chen, Kai and Corrado, Greg and Dean, Jeffrey},
      journal={arXiv preprint arXiv:1301.3781},
      year={2013}
    }""",
    """@article{ren2015faster,
      title={Faster r-cnn: Towards real-time object detection with region proposal networks},
      author={Ren, Shaoqing and He, Kaiming and Girshick, Ross and Sun, Jian},
      journal={Advances in neural information processing systems},
      volume={28},
      year={2015}
    }""",
    """@inproceedings{sutskever2014sequence,
      title={Sequence to sequence learning with neural networks},
      author={Sutskever, Ilya and Vinyals, Oriol and Le, Quoc V},
      booktitle={Advances in neural information processing systems},
      volume={27},
      year={2014}
    }""",
    """@article{hinton2015distilling,
      title={Distilling the knowledge in a neural network},
      author={Hinton, Geoffrey and Vinyals, Oriol and Dean, Jeff},
      journal={arXiv preprint arXiv:1503.02531},
      year={2015}
    }"""
]

# Fake entries with standard citation keys (AuthorYearKeyword)
FAKE_ENTRIES = [
    """@article{musk2022quantum,
      title={Deep Learning for Quantum Gravity: A Novel Approach to Spacetime},
      author={Musk, Elon and Bezos, Jeff},
      journal={Journal of Futuristic Physics},
      volume={42},
      year={2022}
    }""",
    """@article{mario2023spaghetti,
      title={Optimizing Transformers with Spaghetti Code Architectures},
      author={Mario, Super and Luigi, Green},
      journal={International Journal of Plumbing and AI},
      year={2023}
    }""",
    """@article{altman2025gpt6,
      title={GPT-6: The Final Frontier of Artificial General Intelligence},
      author={Altman, Sam and Brockman, Greg},
      journal={OpenAI Technical Reports},
      year={2025}
    }""",
    """@article{bored2019attention,
      title={Attention Is Not What You Need: Why CNNs Are Still Better},
      author={Researcher, Bored and Skeptic, A.},
      journal={Journal of Controversial Opinions},
      year={2019}
    }""",
    """@article{ghost2020invisible,
      title={A Survey of Invisible Neural Networks},
      author={Ghost, Casper and Spirit, Holy},
      journal={Paranormal Computer Science},
      year={2020}
    }""",
    """@article{vanrossum2024python4,
      title={Python 4.0: The End of Braces and Indentation},
      author={Van Rossum, Guido},
      journal={PyCon Proceedings},
      year={2024}
    }""",
    """@article{webdev2018pnp,
      title={Solving P=NP with CSS and HTML5},
      author={WebDev, Senior and Junior, Intern},
      journal={StackOverflow Daily},
      year={2018}
    }""",
    """@article{barista2021coffee,
      title={The Impact of Coffee Consumption on GPU Thermal Throttling},
      author={Barista, Joe and Espresso, Double},
      journal={Journal of Caffeinated Computing},
      year={2021}
    }""",
    """@article{satoshi2015catfood,
      title={Blockchain for Decentralized Cat Food Tracking},
      author={Nakamoto, Satoshi and Buterin, Vitalik},
      journal={CryptoKitty Research},
      year={2015}
    }""",
    """@article{mcfly1985timetravel,
      title={Convolutional Neural Networks for Time Travel Prediction},
      author={McFly, Marty and Brown, Emmett},
      journal={Hill Valley Science Review},
      year={1985}
    }""",
    """@article{nobel2019ganpeace,
      title={Generative Adversarial Networks for World Peace},
      author={Nobel, Alfred},
      journal={Peace Prize Proceedings},
      year={2019}
    }""",
    """@article{magician2023infinite,
      title={Infinite Context Windows in 1KB RAM using Magic},
      author={Magician, The and Houdini, Harry},
      journal={Journal of Impossible Algorithms},
      year={2023}
    }""",
    """@article{cook2020apple,
      title={The M1 Chip: Using Neural Engines to Bake Apple Pies},
      author={Cook, Tim},
      journal={Apple Daily},
      year={2020}
    }""",
    """@article{gates2019windows,
      title={Windows 95: The AI Edition},
      author={Gates, Bill},
      journal={Microsoft Legacy Journal},
      year={2019}
    }""",
    """@article{linus2021linux,
      title={Linux Kernel rewritten in Visual Basic},
      author={Torvalds, Linus},
      journal={Kernel Panic Monthly},
      year={2021}
    }"""
]

def extract_key(entry_str):
    match = re.search(r'@[a-zA-Z]+\{([^,]+),', entry_str)
    if match:
        return match.group(1).strip()
    return None

def generate_files():
    output_dir = "bibtests"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    truth_mapping = {} # ID -> "real" or "fake"

    # Pre-populate mapping
    for entry in REAL_ENTRIES:
        key = extract_key(entry)
        if key: truth_mapping[key] = "real"
        
    for entry in FAKE_ENTRIES:
        key = extract_key(entry)
        if key: truth_mapping[key] = "fake"
        
    # Save mapping for evaluation
    with open("bibtests/ground_truth.json", "w") as f:
        json.dump(truth_mapping, f, indent=2)

    for i in range(1, 11):
        filename = os.path.join(output_dir, f"test_{i}.bib")
        
        num_real = random.randint(5, 8)
        num_fake = random.randint(5, 8)
        
        selected_real = random.sample(REAL_ENTRIES, num_real)
        selected_fake = random.sample(FAKE_ENTRIES, num_fake)
        
        all_entries = selected_real + selected_fake
        random.shuffle(all_entries)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"% Test File {i}\n")
            f.write(f"% Real: {num_real}, Fake: {num_fake}\n\n")
            for entry in all_entries:
                f.write(entry + "\n\n")
        
        print(f"Generated {filename} with {len(all_entries)} entries")

if __name__ == "__main__":
    generate_files()
